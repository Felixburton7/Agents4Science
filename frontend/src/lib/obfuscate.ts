// Deterministically swap the first letter of the first and last name in a PI's
// real name with a different consonant. Reads natural, signals "illustrative"
// rather than impersonating a real person. Geoff Hinton -> Deoff Trinton.
//
// The institutions.json file already contains hand-picked display names so the
// reader sees consistent obfuscated names. This helper exists for fallbacks
// (e.g. PIs returned by the real backend that lack a pre-baked display name).

const SUBS: Record<string, string> = {
  A: "L", B: "R", C: "M", D: "T", E: "K", F: "B", G: "D",
  H: "T", I: "U", J: "N", K: "B", L: "K", M: "T", N: "B",
  O: "I", P: "B", Q: "X", R: "P", S: "L", T: "G", U: "O",
  V: "Y", W: "H", X: "Q", Y: "K", Z: "S",
};

export function obfuscateName(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length < 2) return name;
  const swap = (word: string) => {
    if (!word.length) return word;
    const first = word[0].toUpperCase();
    const sub = SUBS[first] ?? first;
    const cased = word[0] === word[0].toUpperCase() ? sub : sub.toLowerCase();
    return cased + word.slice(1);
  };
  const first = swap(parts[0]);
  const last = swap(parts[parts.length - 1]);
  if (parts.length === 2) return `${first} ${last}`;
  return [first, ...parts.slice(1, -1), last].join(" ");
}
