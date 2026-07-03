import { UPGRADE_URL } from "../config/branding";

function buildUrl(email) {
  if (!email) return UPGRADE_URL;
  const url = new URL(UPGRADE_URL);
  url.searchParams.set("email", email);
  return url.toString();
}

export default function UpgradeButton({ children = "Upgrade →", className = "fp-btn-upgrade", style, email }) {
  return (
    <a
      href={buildUrl(email)}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      style={{ ...style, textDecoration: "none", display: "inline-block", textAlign: "center" }}
    >
      {children}
    </a>
  );
}
