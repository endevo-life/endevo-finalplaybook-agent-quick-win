import { UPGRADE_URL } from "../config/branding";

export default function UpgradeButton({ children = "Upgrade →", className = "fp-btn-upgrade", style }) {
  return (
    <a
      href={UPGRADE_URL}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      style={{ ...style, textDecoration: "none", display: "inline-block", textAlign: "center" }}
    >
      {children}
    </a>
  );
}
