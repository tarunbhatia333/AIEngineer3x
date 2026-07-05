const THEMES = [
  { key: "blue", color: "#5b8cff" },
  { key: "orange", color: "#ff9f43" },
  { key: "green", color: "#22c55e" },
];

export default function ThemeSwitcher({ theme, onChange }) {
  return (
    <div className="theme-switcher">
      {THEMES.map((t) => (
        <button
          key={t.key}
          type="button"
          className={"theme-swatch" + (theme === t.key ? " theme-swatch--active" : "")}
          style={{ background: t.color }}
          onClick={() => onChange(t.key)}
          aria-label={`${t.key} theme`}
          title={`${t.key} theme`}
        />
      ))}
    </div>
  );
}
