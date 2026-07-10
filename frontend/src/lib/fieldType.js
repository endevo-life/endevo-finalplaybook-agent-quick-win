// Infer the right input type from a field's key/label, so "Date set up" gets a
// real date picker, phone fields get a tel keypad, emails an email keyboard,
// etc. Content only carries {key, label}; this keeps the UX smart without
// needing every field to declare a type.
//
// IMPORTANT: match only WHOLE words / camelCase suffixes — an earlier version's
// `\bon\b` matched "pers(on)'s" and turned the name field into a date picker.
// A field key is camelCase (e.g. legacyContactSetupDate), so we also check for a
// "Date"/"Phone"/"Email" suffix in the raw key.
export function fieldInputType(f) {
  const key = f.key || "";
  const label = (f.label || "").toLowerCase();
  const isDate = /Date$|Date[A-Z]/.test(key) || /\bdate\b|\bexpiry\b|\bexpires\b|\bdeadline\b/.test(label);
  const isPhone = /Phone$|Phone[A-Z]|Mobile$/.test(key) || /\bphone\b|\bmobile\b|\bcell\b/.test(label);
  const isEmail = /Email$|Email[A-Z]/.test(key) || /\bemail\b|\be-mail\b/.test(label);
  if (isDate) return "date";
  if (isPhone) return "tel";
  if (isEmail) return "email";
  return "text";
}
