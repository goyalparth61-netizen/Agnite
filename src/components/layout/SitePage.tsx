import type { ReactNode } from "react";
import { ArrowUpRight } from "lucide-react";
import Navbar from "./Navbar";
import Footer from "./Footer";

type SitePageProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  primaryHref?: string;
  primaryLabel?: string;
  secondaryHref?: string;
  secondaryLabel?: string;
};

export default function SitePage({
  eyebrow,
  title,
  description,
  children,
  primaryHref = "#/workspace",
  primaryLabel = "Open Dashboard",
  secondaryHref = "#/",
  secondaryLabel = "Back Home",
}: SitePageProps) {
  return (
    <>
      <a className="skip-link" href="#page-main">Skip to content</a>
      <Navbar />
      <main id="page-main" className="site-page">
        <section className="page-hero container">
          <span className="eyebrow"><span className="short-line" /> {eyebrow}</span>
          <h1>{title}</h1>
          <p>{description}</p>
          <div className="actions">
            <a className="button primary" href={primaryHref}>{primaryLabel} <ArrowUpRight size={16} /></a>
            <a className="button secondary" href={secondaryHref}>{secondaryLabel}</a>
          </div>
        </section>
        <div className="page-content">{children}</div>
      </main>
      <Footer />
    </>
  );
}
