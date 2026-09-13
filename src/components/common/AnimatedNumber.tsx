import { useEffect, useRef, useState } from "react";
import { animate, useInView, useReducedMotion } from "framer-motion";
export default function AnimatedNumber({
  value,
  suffix = "",
}: {
  value: number;
  suffix?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const visible = useInView(ref, { once: true });
  const reduced = useReducedMotion();
  const [number, setNumber] = useState(value);
  useEffect(() => {
    if (!visible || reduced) {
      setNumber(value);
      return;
    }
    const control = animate(0, value, {
      duration: 1.2,
      onUpdate: (n) => setNumber(Math.round(n)),
    });
    return () => control.stop();
  }, [visible, reduced, value]);
  return (
    <span ref={ref} title={value.toLocaleString("en-IN")}>
      {new Intl.NumberFormat("en-IN", {
        notation: value >= 10000 ? "compact" : "standard",
        maximumFractionDigits: 1,
      }).format(number)}
      {suffix}
    </span>
  );
}
