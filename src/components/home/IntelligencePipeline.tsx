import { motion, useReducedMotion } from "framer-motion";
import { pipeline } from "../../data/homeData";
export default function IntelligencePipeline() {
  const reduced = useReducedMotion();
  return (
    <section className="pipeline container" aria-label="Intelligence pipeline">
      {pipeline.map(([title, text], i) => (
        <motion.div
          key={title}
          initial={reduced ? false : { opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.1 }}
        >
          <span className="phase">0{i + 1}</span>
          <h3>{title}</h3>
          <p>{text}</p>
          {i < 5 && <span className="pipeline-arrow">&rarr;</span>}
        </motion.div>
      ))}
    </section>
  );
}
