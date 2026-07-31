import logoSrc from "../../../assets/logo.png";

/**
 * Operator brand logo (SCLERA AI wordmark).
 */
export default function BrandLogo({
  className = "h-11 w-auto max-w-[11rem]",
  alt = "SCLERA AI",
}) {
  return (
    <img
      src={logoSrc}
      alt={alt}
      className={`object-contain object-left ${className}`}
    />
  );
}
