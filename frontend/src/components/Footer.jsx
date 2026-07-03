import { FOOTER_LOGO_URL } from "../config/branding";

export default function Footer() {
  return (
    <div className="fp-footer">
      <span>My Final Playbook</span>
      <span className="fp-footer-sep">·</span>
      <span>Powered by</span>
      {FOOTER_LOGO_URL ? (
        <img src={FOOTER_LOGO_URL} alt="ENDevo" className="fp-footer-logo" />
      ) : (
        <strong>ENDevo</strong>
      )}
    </div>
  );
}
