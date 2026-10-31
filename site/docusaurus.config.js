// Docusaurus configuration for the gitma2 site. Keep this file CommonJS (no "type": "module" in
// package.json): Docusaurus's SSR build breaks otherwise (gitma gotcha).
const config = {
  title: "TMA via ML, second attempt",
  tagline: "Physics does the numerics, learning does the judgement",
  url: "https://debrief.github.io",
  baseUrl: "/gitma2/",
  organizationName: "debrief",
  projectName: "gitma2",
  trailingSlash: false,
  onBrokenLinks: "throw",
  i18n: { defaultLocale: "en", locales: ["en"] },
  markdown: { mermaid: false, hooks: { onBrokenMarkdownLinks: "warn" } },
  presets: [
    [
      "classic",
      {
        docs: { path: "docs", routeBasePath: "/", sidebarPath: "./sidebars.js" },
        blog: { path: "blog", routeBasePath: "blog", blogSidebarCount: "ALL" },
        theme: { customCss: "./src/css/custom.css" },
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: "gitma2",
      items: [
        { to: "/", label: "Welcome", position: "left" },
        { to: "/glossary", label: "Glossary", position: "left" },
        { to: "/data-dictionary", label: "Data dictionary", position: "left" },
        { to: "/blog", label: "Blog", position: "left" },
        { href: "https://github.com/debrief/gitma2", label: "GitHub", position: "right" },
      ],
    },
    footer: {
      style: "dark",
      copyright: `Mock data only; nothing above OFFICIAL. Apache-2.0.`,
    },
  },
};

module.exports = config;
