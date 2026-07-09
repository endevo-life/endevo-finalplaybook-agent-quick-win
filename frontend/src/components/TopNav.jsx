import { COMPANY_NAME, PRODUCT_NAME } from "../config/branding";
import Logo from "./Logo";

export default function TopNav({ route, user, account, onHome, onSignIn, onSignOut, onSettings }) {
  return (
    <div className="fp-topnav">
      <div className="fp-topnav-brand" onClick={onHome}>
        <Logo size={30} radius={8} fontSize={13} />
        <span className="fp-topnav-name">{COMPANY_NAME}</span>
        {PRODUCT_NAME !== COMPANY_NAME && <span className="fp-topnav-sub">· {PRODUCT_NAME}</span>}
      </div>

      <div className="fp-topnav-user">
        {account ? (
          <>
            <span className={`fp-tier-pill ${account.tier === "paid" ? "paid" : ""}`}>
              {account.tier === "paid" ? "Personalized" : "Free"}
            </span>
            <button className="fp-btn-back" onClick={onSettings} title="Account settings">
              <span className="fp-avatar" style={{ cursor: "pointer" }}>{account.email.charAt(0).toUpperCase()}</span>
            </button>
            <button className="fp-btn-back" onClick={onSettings}>settings</button>
            <button className="fp-btn-back" onClick={onSignOut}>sign out</button>
          </>
        ) : (
          <>
            {user?.name && route !== "welcome" && route !== "landing" && (
              <>
                <div className="fp-avatar">{user.name.charAt(0).toUpperCase()}</div>
                <span className="fp-dim">{user.name}</span>
              </>
            )}
            <button className="fp-btn-back" onClick={onSignIn}>sign in</button>
          </>
        )}
      </div>
    </div>
  );
}
