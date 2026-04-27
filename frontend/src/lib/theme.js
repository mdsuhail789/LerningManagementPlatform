/** @typedef {'blue'|'purple'|'green'|'orange'|'teal'} ThemeKey */

/** @type {Record<ThemeKey, { bar: string; soft: string; btn: string; text: string; ring: string }>} */
export const themes = {
  blue: {
    bar: "bg-blue-500",
    soft: "bg-blue-100 text-blue-700",
    btn: "bg-blue-600 hover:bg-blue-700 text-white",
    text: "text-blue-600",
    ring: "ring-blue-500",
  },
  purple: {
    bar: "bg-violet-500",
    soft: "bg-violet-100 text-violet-700",
    btn: "bg-violet-600 hover:bg-violet-700 text-white",
    text: "text-violet-600",
    ring: "ring-violet-500",
  },
  green: {
    bar: "bg-emerald-500",
    soft: "bg-emerald-100 text-emerald-700",
    btn: "bg-emerald-600 hover:bg-emerald-700 text-white",
    text: "text-emerald-600",
    ring: "ring-emerald-500",
  },
  orange: {
    bar: "bg-amber-500",
    soft: "bg-amber-100 text-amber-800",
    btn: "bg-amber-500 hover:bg-amber-600 text-white",
    text: "text-amber-600",
    ring: "ring-amber-500",
  },
  teal: {
    bar: "bg-teal-500",
    soft: "bg-teal-100 text-teal-700",
    btn: "bg-teal-600 hover:bg-teal-700 text-white",
    text: "text-teal-600",
    ring: "ring-teal-500",
  },
};

/** @param {string} key */
export function getTheme(key) {
  return themes[/** @type {ThemeKey} */ (key)] || themes.blue;
}
