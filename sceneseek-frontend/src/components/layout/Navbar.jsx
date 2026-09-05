// sceneseek-frontend/src/components/layout/Navbar.jsx

export default function Navbar({ activePage, onNavigate }) {
  const links = [
    { key: "home", label: "Home" },
    { key: "data", label: "Data" },
    { key: "event", label: "Event" },
  ];

  return (
    <nav className="ss-navbar">
      <span className="ss-navbar__brand">🔭 SceneSeek</span>
      <div className="ss-navbar__links">
        {links.map((link) => (
          <button
            key={link.key}
            className={`ss-navbar__link ${activePage === link.key ? "ss-navbar__link--active" : ""}`}
            onClick={() => onNavigate(link.key)}
          >
            {link.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
