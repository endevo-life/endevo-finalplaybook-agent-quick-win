import {
  faScaleBalanced,
  faSackDollar,
  faHeartPulse,
  faLaptop,
} from "@fortawesome/free-solid-svg-icons";

// Design tokens -- Deep Navy / Gold. Single source of truth mirrored into CSS
// custom properties in global.css (keep both in sync if changed).
export const T = {
  bg: "#FAFAF9",
  surf: "#FFFFFF",
  surf2: "#F2F0EC",
  ink: "#161F33",
  body: "#4A5468",
  dim: "#8B92A3",
  line: "#E3E1D9",
  brand: "#1B2A4A",   // deep navy -- structural/primary actions
  brandLt: "#E9E2D2", // pale warm-gold tint -- selected-state backgrounds
  accent: "#B08D57",  // warm gold -- reserved for upgrade/premium CTAs
  danger: "#A6423A",
};

// Domain labels/colors for grouping the deterministic action items returned
// by /api/plan. Presentation metadata only -- the domain classification
// itself lives in knowledge-base/niki-content-library.json (draft, see
// _meta.status), this file just assigns a color/icon per domain key. `icon`
// holds a Font Awesome icon descriptor object (not JSX) -- consuming
// components render it via <FontAwesomeIcon icon={...} />.
export const DOMAINS = {
  legal: { label: "Legal", color: "#8A6D3B", icon: faScaleBalanced },
  financial: { label: "Financial", color: "#2F6F4F", icon: faSackDollar },
  health: { label: "Physical (health and care)", color: "#9B3B4A", icon: faHeartPulse },
  digital: { label: "Digital", color: "#3E6B8A", icon: faLaptop },
};

export const DOMAIN_ORDER = ["legal", "financial", "health", "digital"];
