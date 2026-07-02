export default function ProgressBar({ doneCount, totalCount }) {
  const pct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;
  return (
    <div>
      <p className="fp-progress-label">{doneCount} of {totalCount} action items checked off</p>
      <div className="fp-progress-bar-wrap">
        <div className="fp-progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
