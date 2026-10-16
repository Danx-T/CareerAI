import { Link } from 'react-router-dom';
import { useEffect, useRef } from 'react';
import { Zap, FileText, MessageSquare, ArrowRight, CheckCircle, TrendingUp } from 'lucide-react';

/* ── Animated floating dot background ─────────────────────── */
function ParticleCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const resize = () => {
      canvas.width  = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const PARTICLE_COUNT = 48;
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x:  Math.random() * canvas.width,
      y:  Math.random() * canvas.height,
      r:  1 + Math.random() * 2,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      a:  0.3 + Math.random() * 0.4,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(20,184,166,${p.a})`;
        ctx.fill();
      });

      // Draw soft connecting lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 110) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(20,184,166,${0.12 * (1 - dist / 110)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize); };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />;
}

/* ── Feature card ──────────────────────────────────────────── */
function FeatureCard({ icon: Icon, title, desc, tealIcon, delay }) {
  return (
    <div
      className="card-hover group animate-slide-up"
      style={{ animationDelay: delay }}
    >
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-5 transition-transform duration-300 group-hover:scale-110 ${
        tealIcon ? 'bg-teal-100' : 'bg-ink-100'
      }`}>
        <Icon className={`w-6 h-6 ${tealIcon ? 'text-teal-600' : 'text-ink-600'}`} />
      </div>
      <h3 className="text-ink-900 font-bold text-base mb-2">{title}</h3>
      <p className="text-ink-500 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

const features = [
  {
    icon: FileText,
    title: 'CV Optimization',
    desc: 'Upload your CV, paste a job description — get an AI-tailored version with a keyword match score.',
    tealIcon: true,
  },
  {
    icon: MessageSquare,
    title: 'Interview Coach',
    desc: 'Practice with AI-generated role-specific questions and get instant, detailed feedback on every answer.',
    tealIcon: false,
  },
  {
    icon: TrendingUp,
    title: 'Performance Reports',
    desc: 'Track your interview scores and see improvement across sessions with category-by-category insights.',
    tealIcon: false,
  },
];

const benefits = [
  'Tailored to the exact job description',
  'Role-specific interview questions',
  'Instant AI feedback on every answer',
  'Comprehensive performance reports',
  'Missing keyword detection',
  'Section-by-section scoring',
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-white overflow-hidden">

      {/* ── Navbar ───────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 flex items-center justify-between
                      bg-white/90 backdrop-blur-md border-b border-ink-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-ink-900 text-base">CareerAI</span>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/login" className="btn-ghost text-sm py-2">Sign In</Link>
          <Link to="/register" className="btn-primary text-sm py-2.5 px-5">Get Started Free</Link>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-24 px-6 overflow-hidden">
        {/* Particle canvas */}
        <div className="absolute inset-0 bg-gradient-to-br from-teal-50/60 via-white to-white">
          <ParticleCanvas />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Pill badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-teal-50 border border-teal-200 text-teal-700 text-sm font-medium mb-8 animate-fade-in">
            <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
            AI-Powered Career Coaching
          </div>

          <h1 className="text-5xl md:text-7xl font-black text-ink-900 leading-tight mb-6 text-balance animate-slide-up">
            Get hired{' '}
            <span className="relative inline-block">
              <span className="text-teal-600">faster</span>
              {/* Underline accent */}
              <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 200 8" preserveAspectRatio="none" height="8">
                <path d="M0,6 Q50,0 100,5 Q150,10 200,4" stroke="#14b8a6" strokeWidth="3" fill="none" strokeLinecap="round" />
              </svg>
            </span>
          </h1>

          <p className="text-xl text-ink-500 max-w-xl mx-auto mb-10 leading-relaxed animate-slide-up stagger-2">
            Optimize your CV for any role and ace the interview with an AI coach that gives real, personalized feedback.
          </p>

          <div className="flex items-center justify-center gap-3 flex-wrap animate-slide-up stagger-3">
            <Link to="/register" className="btn-primary text-base px-8 py-4">
              Start For Free <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/login" className="btn-secondary text-base px-8 py-4">
              Sign In
            </Link>
          </div>

          {/* Social proof row */}
          <p className="text-ink-400 text-sm mt-8 animate-fade-in stagger-4">
            No credit card required · Free to use
          </p>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-ink-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold text-ink-900 mb-3">
              Everything in one place
            </h2>
            <p className="text-ink-500 max-w-lg mx-auto">
              From polishing your CV to acing the interview — CareerAI covers every step.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <FeatureCard key={f.title} {...f} delay={`${i * 0.1}s`} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Benefits ─────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-ink-900 mb-3">Why CareerAI?</h2>
            <p className="text-ink-500">Everything a professional career coach gives you, available instantly.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {benefits.map((b, i) => (
              <div key={b} className="flex items-center gap-3 animate-slide-up" style={{ animationDelay: `${i * 0.06}s` }}>
                <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-4 h-4 text-teal-600" />
                </div>
                <span className="text-ink-700 text-sm font-medium">{b}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-teal-600 relative overflow-hidden">
        {/* Subtle dot grid overlay */}
        <div className="absolute inset-0 bg-dot-grid bg-dot opacity-20" />
        <div className="relative max-w-2xl mx-auto text-center">
          <h2 className="text-4xl font-black text-white mb-4">Ready to land your next role?</h2>
          <p className="text-teal-100 mb-8 text-lg">Join thousands of job seekers already using CareerAI.</p>
          <Link to="/register" className="inline-flex items-center gap-2 px-10 py-4 bg-white text-teal-700 font-bold rounded-xl shadow-card-lg hover:shadow-card transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]">
            Create Free Account <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="border-t border-ink-100 py-8 px-6 text-center text-ink-400 text-sm bg-white">
        © 2025 CareerAI · CV Optimization &amp; Interview Coach
      </footer>
    </div>
  );
}
