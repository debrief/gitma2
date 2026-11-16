// PR previews (spec 022): every pull request's site, built at its head and kept at
// /gitma2/pr/<n>/ after it is merged or closed, with links to the blog posts it delivered.
// The index (pr/index.json) lives at the published root and is updated by
// .github/workflows/pages.yml, so this page reads it from the root whatever build it is in.
import React, { useEffect, useState } from "react";
import Layout from "@theme/Layout";
import BrowserOnly from "@docusaurus/BrowserOnly";

const ROOT = "/gitma2/";
const STATE_STYLE = {
  open: { background: "#2da44e", color: "white" },
  merged: { background: "#8250df", color: "white" },
  closed: { background: "#6e7781", color: "white" },
};

function when(s) {
  return s ? s.replace("T", " ").replace("Z", " UTC") : "";
}

function Index() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("");
  useEffect(() => {
    fetch(window.location.origin + ROOT + "pr/index.json", { cache: "no-store" })
      .then((r) => {
        if (r.status === 404) return { previews: [] };
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(String(e.message || e)));
  }, []);
  if (error) return <p>The preview index could not be read: {error}</p>;
  if (!data) return <p>Loading the preview index…</p>;
  const shown = data.previews.filter((e) => !filter || `${e.number} ${e.title}`.toLowerCase().includes(filter.toLowerCase()));
  return (
    <>
      <p>
        Each pull request from this repository publishes a copy of the site as it stood at the PR's head commit. The copy is
        kept after the PR is merged or closed, so its links stay valid. The blog posts listed are those the PR added or
        changed: the reports of the work it delivered.{" "}
        {data.updated_at && <small>Index updated {when(data.updated_at)}.</small>}
      </p>
      <input type="search" placeholder="filter by number or title" value={filter} onChange={(e) => setFilter(e.target.value)} style={{ padding: "0.3rem 0.5rem", margin: "0.5rem 0 1rem", width: "100%", maxWidth: 360 }} data-testid="filter" />
      {shown.length === 0 ? (
        <p>No previews yet.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }} data-testid="previews">
          {shown.map((e) => (
            <li key={e.number} style={{ borderBottom: "1px solid var(--ifm-color-emphasis-200)", padding: "0.7rem 0" }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "baseline" }}>
                <span className="badge" style={STATE_STYLE[e.state] || {}}>{e.state}</span>
                <strong>#{e.number}</strong>
                <span>{e.title}</span>
              </div>
              <div style={{ fontSize: "0.85rem", marginTop: "0.3rem" }}>
                {e.path ? <a href={ROOT + e.path}>open the preview</a> : <span>no preview was built</span>}
                {e.url && <> · <a href={e.url}>the pull request</a></>}
                {e.head && <> · built at <code>{e.head.slice(0, 7)}</code>, {when(e.built_at)}</>}
              </div>
              {e.posts && e.posts.length > 0 && (
                <ul style={{ fontSize: "0.9rem", marginTop: "0.3rem" }}>
                  {e.posts.map((p) => (
                    <li key={p.path}>
                      <a href={ROOT + e.path + p.path}>{p.title}</a> <small>({p.date})</small>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export default function PreviewsPage() {
  return (
    <Layout title="PR previews" description="Every pull request's site and its reports, kept after the PR completes">
      <div className="container margin-vert--lg" style={{ maxWidth: 900 }}>
        <h1>PR previews</h1>
        <BrowserOnly fallback={<p>The index needs JavaScript.</p>}>{() => <Index />}</BrowserOnly>
      </div>
    </Layout>
  );
}
