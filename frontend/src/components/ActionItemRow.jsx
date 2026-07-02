export default function ActionItemRow({ item, done, onToggle }) {
  return (
    <div className="fp-item-row">
      <button
        type="button"
        className={`fp-item-check ${done ? "done" : ""}`}
        onClick={onToggle}
        aria-label={done ? "Mark incomplete" : "Mark complete"}
      >
        {done ? "✓" : ""}
      </button>
      <div>
        <p className={`fp-item-text ${done ? "done" : ""}`}>{item.text}</p>
        {item.script && <p className="fp-item-script">"{item.script}"</p>}
      </div>
    </div>
  );
}
