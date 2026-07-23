// Line icons for the 10 "why now" signal tiles (WhyNow.jsx). One icon per
// signal flag, drawn in the brand stroke style (currentColor, so the tile's
// CSS controls the color in both normal and selected states). Unknown flags
// render nothing, so a new signal added to whyNowSignals.js degrades cleanly.

const ICONS = {
  // Losing someone close — heart
  recentLossInCircle: (
    <path d="M19.5 12.6 12 20l-7.5-7.4a5 5 0 1 1 7.5-6.6 5 5 0 1 1 7.5 6.6" />
  ),
  // Became responsible for someone — adult + child
  becameResponsible: (
    <>
      <circle cx="9" cy="7.8" r="3.1" />
      <path d="M3.8 19.5a5.2 5.2 0 0 1 10.4 0" />
      <circle cx="17.2" cy="9.7" r="2.2" />
      <path d="M14.2 19.5a4.2 4.2 0 0 1 6.5-3.5" />
    </>
  ),
  // Settled an estate — archive box of papers
  settledAnEstate: (
    <>
      <rect x="3.5" y="4.5" width="17" height="4.4" rx="1.2" />
      <path d="M5.5 8.9v8.6a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V8.9" />
      <path d="M10 13h4" />
    </>
  ),
  // A near miss — pulse line
  recentNearMiss: (
    <path d="M3 12.5h4.2l2.3-5.5 4.6 10.5 2.4-5h4.5" />
  ),
  // A major life change — arrows trading places
  majorLifeChange: (
    <>
      <path d="M16.2 3.8 20 7.4l-3.8 3.6" />
      <path d="M20 7.4H7" />
      <path d="M7.8 20.2 4 16.6l3.8-3.6" />
      <path d="M4 16.6h13" />
    </>
  ),
  // A new decade — birthday cake
  thresholdAge: (
    <>
      <path d="M5.5 19.5v-4.7a1.6 1.6 0 0 1 1.6-1.6h9.8a1.6 1.6 0 0 1 1.6 1.6v4.7" />
      <path d="M4 19.5h16" />
      <path d="M9 13.2v-2.4M12 13.2v-2.9M15 13.2v-2.4" />
      <path d="M9 8.2v-.01M12 7.7v-.01M15 8.2v-.01" />
    </>
  ),
  // Digital life outweighs the paper one — cloud
  digitalOutweighs: (
    <path d="M6.8 18.5h10.6a3.8 3.8 0 0 0 .7-7.5 5.5 5.5 0 0 0-10.7-1.5 4.6 4.6 0 0 0-.6 9z" />
  ),
  // Something worth protecting — shield with check
  worthProtecting: (
    <>
      <path d="M12 3.8 5.5 6.2v5.3c0 4.2 2.8 6.9 6.5 8.7 3.7-1.8 6.5-4.5 6.5-8.7V6.2L12 3.8z" />
      <path d="m9.4 11.9 1.9 1.9 3.3-3.5" />
    </>
  ),
  // A story that shook you — newspaper
  publicCaseShook: (
    <>
      <path d="M16.5 5h-10a2 2 0 0 0-2 2v10.5a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V9h-3" />
      <path d="M8 9h5M8 12.5h5M8 16h5" />
    </>
  ),
  // Tired of the unfinished thing — flag: today you start
  tiredOfUnfinished: (
    <>
      <path d="M6 21V4.6" />
      <path d="M6 5.2c1.8-1.2 3.6-1.2 5.4 0s3.6 1.2 5.4 0v8c-1.8 1.2-3.6 1.2-5.4 0S7.8 12 6 13.2" />
    </>
  ),
};

export default function SignalIcon({ flag }) {
  const paths = ICONS[flag];
  if (!paths) return null;
  return (
    <span className="fp-whynow-icon" aria-hidden="true">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {paths}
      </svg>
    </span>
  );
}
