import { useState } from "react";
import { LOGO_URL, LOGO_LETTER, PRODUCT_NAME } from "../config/branding";

// Renders the brand logo image (Jesse's logo at /logo.png), but gracefully
// falls back to the letter badge if LOGO_URL is unset OR the image fails to load
// (e.g. the file hasn't been added yet). So the nav never shows a broken image.
export default function Logo({ size = 30, radius = 8, fontSize = 13 }) {
  const [failed, setFailed] = useState(false);

  if (LOGO_URL && !failed) {
    return (
      <img
        src={LOGO_URL}
        alt={PRODUCT_NAME}
        onError={() => setFailed(true)}
        style={{ width: size, height: size, borderRadius: radius, objectFit: "contain" }}
      />
    );
  }
  return (
    <div className="fp-logo" style={{ width: size, height: size, borderRadius: radius, fontSize }}>
      {LOGO_LETTER}
    </div>
  );
}
