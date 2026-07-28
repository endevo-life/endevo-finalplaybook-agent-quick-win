"""Production store backed by five DynamoDB tables (one per concern)."""
from decimal import Decimal
from typing import Optional

from app.data.store.base import now, month_key


def _to_ddb(obj):
    """Make an arbitrary JSON-ish value safe to store in DynamoDB:
    - float -> Decimal (DynamoDB rejects Python float)
    - drop empty strings and None values (DynamoDB won't store empty strings,
      and we don't want null noise) -- recursively through dicts/lists.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            cv = _to_ddb(v)
            if cv is None or cv == "":
                continue
            out[k] = cv
        return out
    if isinstance(obj, list):
        return [_to_ddb(v) for v in obj]
    return obj


def _from_ddb(obj):
    """Convert DynamoDB Decimals back to int/float for clean JSON responses."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _from_ddb(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_from_ddb(v) for v in obj]
    return obj


# Fixed partition key for the feedback table -- it's an operator inbox read
# newest-first across all members, so one partition sorts instead of scanning.
FEEDBACK_SCOPE = "b2c"


class DynamoStore:
    """Production store backed by SIX DynamoDB tables, one per concern, matching
    the {prefix}{name} convention of the rest of the AWS account (e.g. lros-*).
    Prefix from DDB_TABLE_PREFIX (default "mfp-dev-"):

        {prefix}users     PK email                -> tier, created_at, stripe id
        {prefix}sessions  PK token                -> email, expires_at (TTL)
        {prefix}usage     PK email, SK month       -> personalize_count, chat_count
        {prefix}plans     PK email                -> answers, plan, tracked (paid)
        {prefix}chat      PK email, SK ts          -> role, content  (paid history)
        {prefix}feedback  PK scope, SK ts_id       -> kind, message, rating

    Free users ARE stored (users + usage) -- they're the funnel and we meter their
    3 free AI questions. Anonymous (never-signed-in) visitors are never stored,
    EXCEPT when they submit feedback (they asked to be contacted).
    """

    def __init__(self, prefix: str):
        import boto3  # lazy import: only needed when STORE_BACKEND=dynamodb
        ddb = boto3.resource("dynamodb")
        self.prefix = prefix
        self.t_users = ddb.Table(f"{prefix}users")
        self.t_sessions = ddb.Table(f"{prefix}sessions")
        self.t_usage = ddb.Table(f"{prefix}usage")
        self.t_plans = ddb.Table(f"{prefix}plans")
        self.t_chat = ddb.Table(f"{prefix}chat")
        self.t_feedback = ddb.Table(f"{prefix}feedback")

    # --- users / entitlements ---
    def get_user(self, email: str) -> Optional[dict]:
        item = self.t_users.get_item(Key={"email": email}).get("Item")
        if not item:
            return None
        return {
            "email": item["email"],
            "tier": item.get("tier", "free"),
            "created_at": int(item.get("created_at", 0)),
            "stripe_customer_id": item.get("stripe_customer_id"),
            "paid_until": int(item["paid_until"]) if item.get("paid_until") is not None else None,
            "canceled": bool(item.get("canceled", False)),
        }

    def upsert_user(self, email: str, tier: str = "free", stripe_customer_id: str = None) -> dict:
        expr = "SET tier = :t, created_at = if_not_exists(created_at, :c)"
        vals = {":t": tier, ":c": now()}
        if stripe_customer_id:
            expr += ", stripe_customer_id = :s"
            vals[":s"] = stripe_customer_id
        self.t_users.update_item(
            Key={"email": email}, UpdateExpression=expr, ExpressionAttributeValues=vals,
        )
        return self.get_user(email)

    def set_tier(self, email: str, tier: str, paid_until: int = None, canceled: bool = None) -> None:
        expr = "SET tier = :t, created_at = if_not_exists(created_at, :c)"
        vals = {":t": tier, ":c": now()}
        if paid_until is not None:
            expr += ", paid_until = :pu"
            vals[":pu"] = paid_until
        if canceled is not None:
            expr += ", canceled = :cx"
            vals[":cx"] = canceled
        self.t_users.update_item(
            Key={"email": email}, UpdateExpression=expr, ExpressionAttributeValues=vals,
        )

    def email_for_stripe_customer(self, stripe_customer_id: str) -> Optional[str]:
        # Small scale: a scan is fine. At volume, add a GSI on stripe_customer_id.
        resp = self.t_users.scan(
            FilterExpression="stripe_customer_id = :s",
            ExpressionAttributeValues={":s": stripe_customer_id},
            ProjectionExpression="email",
        )
        items = resp.get("Items", [])
        return items[0]["email"] if items else None

    # --- sessions ---
    def create_session(self, token: str, email: str, ttl_seconds: int) -> None:
        self.t_sessions.put_item(Item={
            "token": token, "email": email, "expires_at": now() + ttl_seconds,
        })

    def get_session_email(self, token: str) -> Optional[str]:
        item = self.t_sessions.get_item(Key={"token": token}).get("Item")
        if not item or int(item.get("expires_at", 0)) < now():
            return None
        return item["email"]

    def delete_session(self, token: str) -> None:
        self.t_sessions.delete_item(Key={"token": token})

    # --- usage metering ---
    def get_usage(self, email: str) -> dict:
        item = self.t_usage.get_item(Key={"email": email, "month": month_key()}).get("Item") or {}
        return {
            "personalize_count": int(item.get("personalize_count", 0)),
            "chat_count": int(item.get("chat_count", 0)),
        }

    def increment_usage(self, email: str, field: str) -> int:
        resp = self.t_usage.update_item(
            Key={"email": email, "month": month_key()},
            UpdateExpression=f"ADD {field} :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(resp["Attributes"][field])

    def reset_usage(self, email: str) -> None:
        self.t_usage.put_item(Item={
            "email": email, "month": month_key(),
            "personalize_count": 0, "chat_count": 0,
        })

    # --- saved plan + progress (paid experience) ---
    def get_plan(self, email: str) -> Optional[dict]:
        item = self.t_plans.get_item(Key={"email": email}).get("Item")
        if not item:
            return None
        item = _from_ddb(item)
        return {
            "answers": item.get("answers", {}),
            "plan": item.get("plan"),
            "tracked": item.get("tracked", {}),
            "narrative": item.get("narrative"),
            "fields": item.get("fields", {}),
            "updated_at": int(item.get("updated_at", 0)),
        }

    def save_plan(self, email: str, answers=None, plan=None, tracked=None, narrative=None, fields=None) -> None:
        # Alias every attribute via #names -- "plan" (and others) are DynamoDB
        # reserved keywords. Sanitize values (float->Decimal, drop empties) first.
        attrs = {"answers": answers, "plan": plan, "tracked": tracked,
                 "narrative": narrative, "fields": fields}
        sets = ["#updated_at = :updated_at"]
        names = {"#updated_at": "updated_at"}
        vals = {":updated_at": now()}
        for key, value in attrs.items():
            if value is not None:
                sets.append(f"#{key} = :{key}")
                names[f"#{key}"] = key
                vals[f":{key}"] = _to_ddb(value)
        self.t_plans.update_item(
            Key={"email": email},
            UpdateExpression="SET " + ", ".join(sets),
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=vals,
        )

    # --- chat history (paid experience) ---
    def get_chat_history(self, email: str, limit: int = 100) -> list:
        resp = self.t_chat.query(
            KeyConditionExpression="email = :e",
            ExpressionAttributeValues={":e": email},
            ScanIndexForward=True,  # oldest first
            Limit=limit,
        )
        return [{"role": i["role"], "content": i["content"]} for i in resp.get("Items", [])]

    def append_chat(self, email: str, role: str, content: str) -> None:
        # SK is a monotonically increasing timestamp+counter so order is stable.
        import time as _t
        ts = f"{now()}#{int(_t.perf_counter()*1e6) % 1_000_000:06d}"
        self.t_chat.put_item(Item={"email": email, "ts": ts, "role": role, "content": content})

    # --- member feedback (help / complaint / survey) ---
    # Fixed partition + sortable SK, same shape as the events table: feedback is
    # always read newest-first across ALL members (an operator inbox, not a
    # per-user history), so one partition queries in order instead of scanning.
    def save_feedback(self, email, kind, message, rating=None, page=None,
                      signed_in=False) -> dict:
        import time as _t
        ts = now()
        sk = f"{ts}#{int(_t.perf_counter()*1e6) % 1_000_000:06d}"
        item = {
            "scope": FEEDBACK_SCOPE, "ts_id": sk, "ts": ts,
            "email": email or "-", "kind": kind, "message": message,
            "signed_in": bool(signed_in),
        }
        if rating is not None:
            item["rating"] = int(rating)
        if page:
            item["page"] = page
        self.t_feedback.put_item(Item=item)
        return {"id": f"fb_{sk}", "email": email, "kind": kind, "message": message,
                "rating": rating, "page": page, "signed_in": bool(signed_in),
                "created_at": ts}

    def list_feedback(self, limit: int = 100, since: int = None) -> list:
        kwargs = {
            "KeyConditionExpression": "#s = :s",
            "ExpressionAttributeNames": {"#s": "scope"},
            "ExpressionAttributeValues": {":s": FEEDBACK_SCOPE},
            "ScanIndexForward": False,  # newest first
            "Limit": limit,
        }
        if since is not None:
            # ts_id is a STRING key ("{epoch}#{counter}"), so this is a
            # lexicographic compare. That matches numeric order only because
            # epoch seconds are a fixed 10 digits (true until 2286) -- don't
            # switch to a shorter/variable timestamp without revisiting this.
            kwargs["KeyConditionExpression"] = "#s = :s AND ts_id >= :since"
            kwargs["ExpressionAttributeValues"][":since"] = str(since)
        resp = self.t_feedback.query(**kwargs)
        out = []
        for i in resp.get("Items", []):
            em = i.get("email")
            out.append({
                "id": f"fb_{i.get('ts_id')}",
                "email": None if em == "-" else em,
                "kind": i.get("kind"), "message": i.get("message"),
                "rating": int(i["rating"]) if i.get("rating") is not None else None,
                "page": i.get("page"), "signed_in": bool(i.get("signed_in")),
                "created_at": int(i.get("ts", 0)),
            })
        return out

    def count_feedback_since(self, email: str, since: int) -> int:
        """Submissions from one email since a timestamp -- powers rate limiting."""
        return sum(1 for f in self.list_feedback(limit=200, since=since)
                   if f.get("email") == email)
