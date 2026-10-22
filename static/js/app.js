(() => {
  const root = document.documentElement;
  const themeButton = document.getElementById("themeToggle");
  const menuButton = document.getElementById("menuToggle");
  const shell = document.getElementById("appShell");

  const savedTheme = localStorage.getItem("biblioteca-theme");
  if (savedTheme === "dark") root.dataset.theme = "dark";

  themeButton?.addEventListener("click", () => {
    const dark = root.dataset.theme !== "dark";
    root.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("biblioteca-theme", dark ? "dark" : "light");
  });

  if (localStorage.getItem("biblioteca-sidebar") === "collapsed") {
    shell?.classList.add("sidebar-collapsed");
  }
  menuButton?.addEventListener("click", () => {
    shell?.classList.toggle("sidebar-collapsed");
    localStorage.setItem("biblioteca-sidebar",
      shell?.classList.contains("sidebar-collapsed") ? "collapsed" : "expanded");
  });
})();
