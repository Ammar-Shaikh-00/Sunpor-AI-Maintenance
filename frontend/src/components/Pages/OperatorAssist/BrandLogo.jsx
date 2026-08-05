import lightLogoSrc from "../../../assets/logo.png";
import darkLogoSrc from "../../../assets/black-theme-logo.png";

/**
 * Operator brand logo (SCLERA AI wordmark).
 * Uses the dark-theme logo when operator theme is dark.
 */
export default function BrandLogo({
  className = "h-11 w-auto max-w-[11rem]",
  alt = "SCLERA AI",
  theme = "dark",
}) {
  const logoSrc = theme === "light" ? lightLogoSrc : darkLogoSrc;

  return (
    <img
      src={logoSrc}
      alt={alt}
      className={`object-contain object-left ${className}`}
    />
  );
}
