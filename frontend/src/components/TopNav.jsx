import { LOGO_URL } from "../config/branding";

export default function TopNav({ route, user, onHome }) {
  return (
    <div className="fp-topnav">
      <div className="fp-topnav-brand" onClick={onHome}>
        {LOGO_URL ? (
          <img src={LOGO_URL} alt="Final Playbook" style={{ width: 30, height: 30, borderRadius: 8, objectFit: "contain" }} />
        ) : (
          <div className="fp-logo">E</div>
        )}
        <span className="fp-topnav-name">ENDevo</span>
        <span className="fp-topnav-sub">· Final Playbook</span>
      </div>
      {user.name && route !== "welcome" && (
        <div className="fp-topnav-user">
          <div className="fp-avatar">{user.name.charAt(0).toUpperCase()}</div>
          <span className="fp-dim">{user.name}</span>
        </div>
      )}
    </div>
  );
}
