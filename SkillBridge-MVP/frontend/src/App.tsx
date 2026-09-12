import { useEffect, useState, type ButtonHTMLAttributes, type FormEvent, type ReactNode } from 'react';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import { Link, Route, Switch, useLocation, useRoute } from 'wouter';
import {
  ArrowRight, Award, BarChart3, BriefcaseBusiness, Check, CheckCircle2, ChevronRight, CircleAlert,
  ClipboardCheck, Clock, Flame, HelpCircle, LayoutDashboard, Lock, LogIn, LogOut, Menu, Network,
  Plus, RefreshCw, Send, Settings, ShieldCheck, Sparkles, Target, Trash2, TrendingUp, User as UserIcon,
  UserCheck, Users, X, XCircle,
} from 'lucide-react';
import {
  customFetch,
  getGetCurrentUserQueryKey, getGetStudentApplicationsQueryKey,
  getGetStudentProfileQueryKey, getGetStudentSkillGapsQueryKey,
  getListMyOpportunitiesQueryKey, getListOpportunitiesQueryKey, getListOpportunityApplicantsQueryKey,
  getListSkillsQueryKey, setAuthTokenGetter, useApplyToOpportunity, useCreateOpportunity,
  useGetAssessment, useGetCurrentUser, useGetInstitutionStats, useGetStudentProfile,
  useGetStudentSkillGaps, useGetStudentApplications, useGetOpportunity, useHealthCheck,
  useListMyOpportunities, useListOpportunities, useListOpportunityApplicants, useListSkills,
  useLoginUser, useRegisterUser, useSubmitAssessment, useUpdateApplicationStatus,
  type Applicant, type InstitutionStats, type Opportunity, type OpportunityWithMatch,
  type ScreeningAttempt, type ScreeningQuestion, type ScreeningSubmissionResult, type ScreeningTest,
  type SkillGap, type User,
} from '@workspace/api-client-react';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import NotFound from '@/pages/not-found';
import './index.css';

setAuthTokenGetter(() => localStorage.getItem('skillbridge_token'));
const queryClient = new QueryClient();

type Role = 'student' | 'industry' | 'academician' | 'institution';

const roleNames: Record<Role, string> = {
  student: 'Student', industry: 'Industry', academician: 'Academician', institution: 'Institution',
};

const roleDescriptions: Record<Role, string> = {
  student: 'Assess your skills, discover gaps, apply to matched opportunities & complete company screening tests.',
  industry: 'Post jobs/internships with required skills, configure custom screening tests, and evaluate candidate readiness.',
  academician: 'Coach learners from skill signals, benchmark readiness, and align educational targets.',
  institution: 'Analyze aggregate student readiness, cohort skill trends, and industry-aligned demand.',
};

function Logo({ dark = false }: { dark?: boolean }) {
  return (
    <Link href="/" className={`inline-flex items-center gap-2.5 ${dark ? 'text-background' : 'text-foreground'}`} data-testid="link-logo">
      <span className={`grid h-9 w-9 place-items-center rounded-xl ${dark ? 'bg-accent text-accent-foreground' : 'bg-primary text-primary-foreground'}`}>
        <Network size={19} strokeWidth={2.4} />
      </span>
      <span className="sb-display text-[1.08rem] font-bold tracking-[-.03em]">skillbridge<span className={dark ? 'text-accent' : 'text-accent'}>.</span></span>
    </Link>
  );
}

function Button({ children, kind = 'primary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { kind?: 'primary' | 'sun' | 'ghost' | 'coral' }) {
  return <button className={`sb-btn sb-btn-${kind} ${className}`} {...props}>{children}</button>;
}

function LoadingBlock({ label = 'Loading signal' }: { label?: string }) {
  return <div className="sb-card flex min-h-36 items-center justify-center gap-3 p-8 text-sm text-muted-foreground" data-testid="status-loading">
    <span className="h-2 w-2 animate-pulse rounded-full bg-accent" /><span>{label}</span>
  </div>;
}

function ErrorBlock({ onRetry }: { onRetry?: () => void }) {
  return <div className="sb-card flex min-h-36 flex-col items-center justify-center gap-3 p-8 text-center" data-testid="status-error">
    <CircleAlert className="text-accent" size={22} /><p className="text-sm text-muted-foreground">We could not reach this signal right now.</p>
    {onRetry && <Button kind="ghost" onClick={onRetry}><RefreshCw size={15} /> Try again</Button>}
  </div>;
}

function EmptyBlock({ title, text, action }: { title: string; text: string; action?: ReactNode }) {
  return <div className="sb-card flex min-h-44 flex-col items-center justify-center p-8 text-center" data-testid="status-empty">
    <div className="mb-3 grid h-10 w-10 place-items-center rounded-full bg-secondary text-primary"><Sparkles size={17} /></div>
    <p className="font-semibold">{title}</p><p className="mt-1 max-w-sm text-sm text-muted-foreground">{text}</p>{action && <div className="mt-4">{action}</div>}
  </div>;
}

function getPasswordStrength(pwd: string) {
  const checks = [
    { label: 'At least 8 characters', passed: pwd.length >= 8 },
    { label: 'Contains lowercase letter', passed: /[a-z]/.test(pwd) },
    { label: 'Contains uppercase letter', passed: /[A-Z]/.test(pwd) },
    { label: 'Contains number or symbol', passed: /[0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd) },
  ];
  const passedCount = checks.filter((c) => c.passed).length;
  let score = 0;
  let label = 'Empty';
  let color = 'bg-muted';
  if (pwd.length > 0) {
    if (pwd.length < 6) {
      score = 1;
      label = 'Too short';
      color = 'bg-red-500';
    } else if (passedCount <= 1) {
      score = 1;
      label = 'Weak';
      color = 'bg-red-500';
    } else if (passedCount === 2) {
      score = 2;
      label = 'Fair';
      color = 'bg-amber-500';
    } else if (passedCount === 3) {
      score = 3;
      label = 'Good';
      color = 'bg-blue-500';
    } else {
      score = 4;
      label = 'Strong';
      color = 'bg-emerald-500';
    }
  }
  return { score, label, color, checks };
}

function AppShell({ user, children, onLogout }: { user?: User; children: ReactNode; onLogout: () => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [, navigate] = useLocation();
  const role = user?.role as Role | undefined;
  const links = role === 'industry'
    ? [{ href: '/industry', label: 'Opportunity desk', icon: BriefcaseBusiness }]
    : role === 'institution' || role === 'academician'
      ? [{ href: '/institution', label: 'Readiness view', icon: BarChart3 }]
      : [{ href: '/student', label: 'My readiness', icon: LayoutDashboard }, { href: '/assessment', label: 'Assessment', icon: ClipboardCheck }];
  return <div className="sb-shell flex min-h-[100dvh]">
    <aside className="hidden w-[258px] shrink-0 flex-col bg-sidebar px-5 py-6 text-sidebar-foreground md:flex">
      <Logo dark />
      <div className="mt-12">
        <p className="sb-mono mb-3 text-[10px] uppercase tracking-[.18em] text-sidebar-foreground/50">Workspace</p>
        <nav className="space-y-1">
          {links.map(({ href, label, icon: Icon }) => <Link href={href} key={href} className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-sidebar-foreground/72 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground" data-testid={`link-nav-${label.toLowerCase().replaceAll(' ', '-')}`}><Icon size={17} /><span>{label}</span><ChevronRight className="ml-auto opacity-40" size={14} /></Link>)}
        </nav>
      </div>
      <div className="mt-auto rounded-xl border border-sidebar-border bg-sidebar-accent/45 p-4">
        <ShieldCheck size={18} className="mb-3 text-sidebar-primary" />
        <p className="text-sm font-semibold">Evidence, not exposure.</p>
        <p className="mt-1 text-xs leading-5 text-sidebar-foreground/58">Readiness signals stay aggregated and purposeful.</p>
      </div>
      <button onClick={onLogout} className="mt-5 flex items-center gap-3 px-3 py-2 text-sm text-sidebar-foreground/60 hover:text-sidebar-foreground" data-testid="button-logout"><LogOut size={16} /> Sign out</button>
    </aside>
    <div className="min-w-0 flex-1">
      <header className="sticky top-0 z-20 flex h-[72px] items-center justify-between border-b border-border bg-background/90 px-5 backdrop-blur md:px-10">
        <button className="md:hidden" onClick={() => setMenuOpen(!menuOpen)} data-testid="button-mobile-menu"><Menu size={21} /></button>
        <div className="md:hidden"><Logo /></div>
        <div className="ml-auto flex items-center gap-3">
          <span className="hidden text-right sm:block">
            <span className="block text-sm font-semibold" data-testid="text-user-name">{user?.name ?? 'Workspace'}</span>
            <span className="text-xs text-muted-foreground">{user ? roleNames[user.role as Role] : 'Preview'}</span>
          </span>
          <span className="grid h-9 w-9 place-items-center rounded-full bg-secondary text-sm font-bold text-primary" data-testid="text-user-initials">{user?.name?.split(' ').map((x) => x[0]).join('').slice(0, 2).toUpperCase() ?? 'SB'}</span>
        </div>
      </header>
      {menuOpen && <div className="border-b border-border bg-sidebar p-4 text-sidebar-foreground md:hidden">
        {links.map(({ href, label }) => <Link href={href} onClick={() => setMenuOpen(false)} key={href} className="block rounded-lg px-3 py-3 text-sm" data-testid={`link-mobile-${label}`}>{label}</Link>)}
        <button onClick={onLogout} className="mt-1 px-3 py-3 text-sm text-sidebar-foreground/70" data-testid="button-mobile-logout">Sign out</button>
      </div>}
      <main className="mx-auto max-w-[1440px] px-5 py-8 md:px-10 md:py-10">{children}</main>
    </div>
  </div>;
}

function Landing() {
  const health = useHealthCheck();
  const [role, setRole] = useState<Role>('student');
  const roleCopy: Record<Role, { kicker: string; title: string; body: string; href: string }> = {
    student: { kicker: 'For students', title: 'Make your evidence count.', body: 'Turn one focused assessment into a clear readiness profile and a better next opportunity.', href: '/register' },
    industry: { kicker: 'For industry teams', title: 'Hire for signal, not polish.', body: 'See the skills behind the application with transparent, skill-based matches.', href: '/register' },
    academician: { kicker: 'For academicians', title: 'Coach from a shared picture.', body: 'Give learners a language for the gap between where they are and where they want to go.', href: '/register' },
    institution: { kicker: 'For institutions', title: 'See readiness, responsibly.', body: 'Understand aggregate skill signals without opening a private student file.', href: '/register' },
  };
  const current = roleCopy[role];
  return <div className="sb-shell sb-noise overflow-hidden">
    <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 md:px-8"><Logo /><div className="flex items-center gap-3"><Link href="/login" className="sb-btn sb-btn-ghost hidden sm:inline-flex" data-testid="link-login">Log in</Link><Link href="/register" className="sb-btn sb-btn-primary" data-testid="link-register">Join SkillBridge <ArrowRight size={15} /></Link></div></header>
    <section className="sb-grid relative mx-4 mt-4 overflow-hidden rounded-[1.5rem] bg-primary px-6 py-16 text-primary-foreground md:mx-8 md:px-16 md:py-24">
      <div className="relative z-10 max-w-3xl sb-enter"><p className="sb-mono mb-6 text-xs uppercase tracking-[.2em] text-primary-foreground/60">A clearer bridge from learning to work</p><h1 className="sb-display max-w-3xl text-5xl font-bold leading-[.96] md:text-7xl">The proof is in your <span className="text-secondary">progress.</span></h1><p className="mt-7 max-w-xl text-base leading-7 text-primary-foreground/72 md:text-lg">SkillBridge connects assessment evidence to opportunity — with enough context for a fair decision, and enough privacy for trust.</p><div className="mt-9 flex flex-wrap gap-3"><Link href="/register" className="sb-btn bg-secondary text-secondary-foreground" data-testid="link-hero-start">Build your bridge <ArrowRight size={16} /></Link><Link href="/login" className="sb-btn border border-primary-foreground/25 text-primary-foreground hover:bg-primary-foreground/10" data-testid="link-hero-login">I already have an account</Link></div></div>
      <div className="pointer-events-none absolute -right-20 -top-20 hidden h-[460px] w-[460px] rounded-full border-[70px] border-secondary/15 md:block" /><div className="pointer-events-none absolute -bottom-28 right-32 hidden h-72 w-72 rotate-12 rounded-[4rem] bg-accent/85 md:block" />
      <div className="absolute bottom-7 right-9 hidden rounded-xl border border-primary-foreground/15 bg-primary-foreground/10 p-4 backdrop-blur md:block"><div className="flex items-center gap-3"><span className="grid h-8 w-8 place-items-center rounded-full bg-secondary text-primary"><TrendingUp size={15} /></span><div><p className="sb-mono text-[10px] uppercase tracking-widest text-primary-foreground/55">Readiness signal</p><p className="text-sm font-bold">Visible. Actionable. Yours.</p></div></div></div>
    </section>
    <section className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28"><div className="grid gap-12 md:grid-cols-[.8fr_1.2fr] md:items-end"><div><p className="sb-mono text-xs uppercase tracking-[.18em] text-accent">Choose your lens</p><h2 className="sb-display mt-4 text-4xl font-bold leading-none md:text-5xl">One bridge.<br />Four ways in.</h2></div><div><p className="max-w-xl text-lg leading-8 text-muted-foreground">The same trusted signal becomes a different kind of advantage depending on where you stand.</p><div className="mt-6 flex flex-wrap gap-2">{(Object.keys(roleCopy) as Role[]).map((item) => <button key={item} onClick={() => setRole(item)} className={`sb-pill border px-4 py-2.5 text-sm ${role === item ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-card text-muted-foreground'}`} data-testid={`button-role-${item}`}>{roleNames[item]}</button>)}</div></div></div>
      <div className="mt-12 grid gap-6 lg:grid-cols-[1.2fr_.8fr]"><div className="sb-card sb-card-lift min-h-[280px] bg-secondary p-7 md:p-10"><p className="sb-mono text-xs uppercase tracking-[.16em] text-primary/55">{current.kicker}</p><h3 className="sb-display mt-8 max-w-lg text-3xl font-bold leading-tight md:text-4xl">{current.title}</h3><p className="mt-4 max-w-md leading-7 text-primary/70">{current.body}</p><Link href={current.href} className="mt-8 inline-flex items-center gap-2 text-sm font-bold text-primary" data-testid="link-role-continue">Continue as {roleNames[role]} <ArrowRight size={15} /></Link></div><div className="sb-card overflow-hidden bg-card p-7 md:p-9"><p className="sb-mono text-xs uppercase tracking-[.16em] text-muted-foreground">The flow</p><div className="mt-7 space-y-5">{[['01', 'Show your signal', 'A 12-question assessment becomes a useful profile.'], ['02', 'Find your fit', 'Opportunities meet the skills you are building.'], ['03', 'Take the next step', 'A shared language makes action easier.']].map(([num, title, text]) => <div className="flex gap-4" key={num}><span className="sb-mono text-xs text-accent">{num}</span><div><p className="font-semibold">{title}</p><p className="mt-1 text-sm leading-6 text-muted-foreground">{text}</p></div></div>)}</div></div></div>
    </section>
    <footer className="border-t border-border px-5 py-8 md:px-8"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 text-sm text-muted-foreground"><Logo /><span>Built for the space between learning and doing.</span><span className="sb-mono text-[10px] uppercase tracking-widest">Signal / Context / Trust</span></div></footer>
  </div>;
}

function Auth({ mode, onAuth }: { mode: 'login' | 'register'; onAuth: (user: User, token?: string) => void }) {
  const [, navigate] = useLocation();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    age: '',
    gender: 'Prefer not to say',
    role: 'student' as Role,
  });
  const [error, setError] = useState('');
  const login = useLoginUser();
  const register = useRegisterUser();
  const pending = login.isPending || register.isPending;
  const strength = getPasswordStrength(form.password);

  const submitLogin = (event: FormEvent) => {
    event.preventDefault();
    setError('');
    login.mutate({ data: { email: form.email, password: form.password } }, {
      onSuccess: (result) => {
        localStorage.setItem('skillbridge_token', result.access_token);
        onAuth(result.user, result.access_token);
        navigate(result.user.role === 'industry' ? '/industry' : result.user.role === 'institution' || result.user.role === 'academician' ? '/institution' : '/student');
      },
      onError: (err) => setError((err as Error).message),
    });
  };

  const submitRegister = (event: FormEvent) => {
    event.preventDefault();
    setError('');
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    const ageNum = form.age ? parseInt(form.age, 10) : undefined;
    register.mutate({
      data: {
        name: form.name,
        email: form.email,
        password: form.password,
        role: form.role,
        age: ageNum && !isNaN(ageNum) ? ageNum : undefined,
        gender: form.gender,
      },
    }, {
      onSuccess: () => {
        // Automatically log in to provide a frictionless onboarding experience
        login.mutate({ data: { email: form.email, password: form.password } }, {
          onSuccess: (result) => {
            localStorage.setItem('skillbridge_token', result.access_token);
            onAuth(result.user, result.access_token);
            navigate(result.user.role === 'industry' ? '/industry' : result.user.role === 'institution' || result.user.role === 'academician' ? '/institution' : '/student');
          },
          onError: () => navigate('/login'),
        });
      },
      onError: (err) => setError((err as Error).message),
    });
  };

  const nextStep = () => {
    setError('');
    if (step === 1) {
      if (!form.email || !form.email.includes('@')) {
        setError('Please enter a valid email address');
        return;
      }
      if (form.password.length < 6) {
        setError('Password must be at least 6 characters long');
        return;
      }
      if (form.password !== form.confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      setStep(2);
    } else if (step === 2) {
      if (!form.name.trim()) {
        setError('Please enter your full name');
        return;
      }
      if (form.age) {
        const a = parseInt(form.age, 10);
        if (isNaN(a) || a < 14 || a > 100) {
          setError('Please provide a valid age between 14 and 100');
          return;
        }
      }
      setStep(3);
    }
  };

  return <div className="sb-shell sb-noise grid min-h-[100dvh] lg:grid-cols-[1fr_1.05fr]">
    <div className="relative hidden overflow-hidden bg-primary p-12 text-primary-foreground lg:flex lg:flex-col">
      <Logo dark />
      <div className="relative z-10 mt-auto max-w-lg pb-10">
        <p className="sb-mono text-xs uppercase tracking-[.2em] text-secondary">A better handoff</p>
        <h1 className="sb-display mt-5 text-6xl font-bold leading-[.95]">Make the next step feel earned.</h1>
        <p className="mt-6 max-w-md text-base leading-7 text-primary-foreground/65">SkillBridge gives every person in the room a clearer view of readiness — without flattening them into a score.</p>
      </div>
      <div className="absolute -bottom-32 -right-24 h-96 w-96 rounded-full border-[60px] border-accent/25" />
    </div>
    <div className="flex items-center justify-center px-5 py-12">
      <div className="w-full max-w-md sb-enter">
        <div className="mb-10 lg:hidden"><Logo /></div>
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground" data-testid="link-auth-back">
          <ChevronRight className="rotate-180" size={15} /> Back to home
        </Link>
        <p className="sb-mono text-xs uppercase tracking-[.18em] text-accent">
          {mode === 'login' ? 'Welcome back' : `Step ${step} of 3 · ${step === 1 ? 'Account Setup' : step === 2 ? 'Personal Details' : 'Choose Role'}`}
        </p>
        <h2 className="sb-display mt-3 text-4xl font-bold">
          {mode === 'login' ? 'Log in to SkillBridge' : step === 1 ? 'Create your credentials' : step === 2 ? 'Tell us about you' : 'Select your workspace'}
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          {mode === 'login' ? 'Your next opportunity is waiting on the other side of a clear signal.' : 'Join students, employers, and institutions building on verified technical skill.'}
        </p>

        {mode === 'register' && (
          <div className="mt-6">
            <div className="flex items-center justify-between gap-2">
              <div className={`flex flex-1 items-center gap-2 pb-2 border-b-2 ${step >= 1 ? 'border-primary text-primary font-bold' : 'border-border text-muted-foreground'} text-xs`}>
                <span className={`grid h-5 w-5 place-items-center rounded-full text-[11px] ${step >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>1</span>
                Account
              </div>
              <div className={`flex flex-1 items-center gap-2 pb-2 border-b-2 ${step >= 2 ? 'border-primary text-primary font-bold' : 'border-border text-muted-foreground'} text-xs`}>
                <span className={`grid h-5 w-5 place-items-center rounded-full text-[11px] ${step >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>2</span>
                Personal
              </div>
              <div className={`flex flex-1 items-center gap-2 pb-2 border-b-2 ${step >= 3 ? 'border-primary text-primary font-bold' : 'border-border text-muted-foreground'} text-xs`}>
                <span className={`grid h-5 w-5 place-items-center rounded-full text-[11px] ${step >= 3 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>3</span>
                Role
              </div>
            </div>
          </div>
        )}

        {mode === 'login' ? (
          <form onSubmit={submitLogin} className="mt-8 space-y-5">
            <div>
              <label className="sb-label" htmlFor="email">Email address</label>
              <input id="email" type="email" className="sb-input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required data-testid="input-email" />
            </div>
            <div>
              <label className="sb-label" htmlFor="password">Password</label>
              <input id="password" type="password" minLength={6} className="sb-input" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required data-testid="input-password" />
            </div>
            {error && <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-accent" data-testid="status-auth-error">{error}</div>}
            <Button type="submit" disabled={pending} className="w-full">
              {pending ? 'Working…' : <><LogIn size={16} /> Log in</>}
            </Button>
          </form>
        ) : (
          <form onSubmit={step === 3 ? submitRegister : (e) => { e.preventDefault(); nextStep(); }} className="mt-7 space-y-5">
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="sb-label" htmlFor="email">Email address</label>
                  <input id="email" type="email" className="sb-input" placeholder="you@example.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required data-testid="input-email" />
                </div>
                <div>
                  <label className="sb-label" htmlFor="password">Password</label>
                  <input id="password" type="password" minLength={6} className="sb-input" placeholder="At least 6 characters" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required data-testid="input-password" />
                  {form.password && (
                    <div className="mt-2.5 rounded-lg border border-border bg-card p-3 text-xs">
                      <div className="flex items-center justify-between mb-1.5 font-medium">
                        <span>Password strength:</span>
                        <span className={`font-semibold ${strength.score >= 3 ? 'text-emerald-600' : strength.score === 2 ? 'text-amber-600' : 'text-red-500'}`}>{strength.label}</span>
                      </div>
                      <div className="grid grid-cols-4 gap-1.5 h-1.5 mb-2">
                        {[1, 2, 3, 4].map((bar) => (
                          <div key={bar} className={`rounded-full ${strength.score >= bar ? strength.color : 'bg-muted'}`} />
                        ))}
                      </div>
                      <div className="grid grid-cols-2 gap-1 text-[11px] text-muted-foreground">
                        {strength.checks.map((c) => (
                          <div key={c.label} className="flex items-center gap-1.5">
                            <span className={c.passed ? 'text-emerald-600' : 'text-muted-foreground/50'}>{c.passed ? '✓' : '•'}</span>
                            <span className={c.passed ? 'text-foreground' : ''}>{c.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <div>
                  <label className="sb-label" htmlFor="confirmPassword">Confirm password</label>
                  <input id="confirmPassword" type="password" minLength={6} className="sb-input" placeholder="Repeat your password" value={form.confirmPassword} onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })} required data-testid="input-confirm-password" />
                  {form.confirmPassword && (
                    <p className={`mt-1 text-xs ${form.password === form.confirmPassword ? 'text-emerald-600' : 'text-accent'}`}>
                      {form.password === form.confirmPassword ? '✓ Passwords match' : '✗ Passwords do not match'}
                    </p>
                  )}
                </div>
                {error && <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-accent" data-testid="status-auth-error">{error}</div>}
                <Button type="button" onClick={nextStep} className="w-full" data-testid="button-next-step-1">
                  Continue to Personal Details <ArrowRight size={16} />
                </Button>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div>
                  <label className="sb-label" htmlFor="name">Full name</label>
                  <input id="name" className="sb-input" placeholder="e.g. Alex Johnson" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required data-testid="input-name" />
                </div>
                <div>
                  <label className="sb-label" htmlFor="age">Age</label>
                  <input id="age" type="number" min={14} max={100} className="sb-input" placeholder="e.g. 21" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} data-testid="input-age" />
                  <p className="mt-1 text-xs text-muted-foreground">Used for demographic insights & employability benchmarks.</p>
                </div>
                <div>
                  <label className="sb-label">Gender</label>
                  <div className="grid grid-cols-2 gap-2">
                    {['Male', 'Female', 'Other', 'Prefer not to say'].map((g) => (
                      <button
                        type="button"
                        key={g}
                        onClick={() => setForm({ ...form, gender: g })}
                        className={`rounded-lg border px-3 py-2.5 text-left text-sm transition-all ${form.gender === g ? 'border-primary bg-secondary font-semibold text-primary' : 'border-border bg-card text-muted-foreground hover:bg-muted'}`}
                        data-testid={`button-gender-${g.toLowerCase().replaceAll(' ', '-')}`}
                      >
                        {g}
                      </button>
                    ))}
                  </div>
                </div>
                {error && <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-accent" data-testid="status-auth-error">{error}</div>}
                <div className="flex gap-3">
                  <Button type="button" kind="ghost" onClick={() => setStep(1)} className="w-1/3">Back</Button>
                  <Button type="button" onClick={nextStep} className="w-2/3" data-testid="button-next-step-2">
                    Continue to Role <ArrowRight size={16} />
                  </Button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <div>
                  <label className="sb-label">I am joining as</label>
                  <div className="grid grid-cols-1 gap-2.5">
                    {(Object.keys(roleNames) as Role[]).map((r) => (
                      <button
                        type="button"
                        key={r}
                        onClick={() => setForm({ ...form, role: r })}
                        className={`rounded-xl border p-3.5 text-left transition-all ${form.role === r ? 'border-primary bg-secondary/80 ring-1 ring-primary' : 'border-border bg-card hover:border-primary/40'}`}
                        data-testid={`button-register-role-${r}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-primary">{roleNames[r]}</span>
                          {form.role === r && <Check size={16} className="text-primary" />}
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">{roleDescriptions[r]}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="rounded-lg border border-border bg-card/60 p-3.5 text-xs text-muted-foreground space-y-1">
                  <div className="font-semibold text-foreground">Registration Summary</div>
                  <div><span className="font-medium text-foreground">Name:</span> {form.name || '—'} · <span className="font-medium text-foreground">Age:</span> {form.age || 'Not specified'} · <span className="font-medium text-foreground">Gender:</span> {form.gender}</div>
                  <div><span className="font-medium text-foreground">Email:</span> {form.email} · <span className="font-medium text-foreground">Role:</span> {roleNames[form.role]}</div>
                </div>

                {error && <div className="rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-accent" data-testid="status-auth-error">{error}</div>}
                <div className="flex gap-3">
                  <Button type="button" kind="ghost" onClick={() => setStep(2)} className="w-1/3">Back</Button>
                  <Button type="submit" disabled={pending} className="w-2/3" data-testid="button-submit-register">
                    {pending ? 'Creating account…' : <>Complete & Enter <ArrowRight size={16} /></>}
                  </Button>
                </div>
              </div>
            )}
          </form>
        )}

        <p className="mt-8 text-center text-sm text-muted-foreground">
          {mode === 'login' ? 'New to SkillBridge? ' : 'Already have an account? '}
          <Link href={mode === 'login' ? '/register' : '/login'} className="font-bold text-primary" data-testid="link-auth-switch">
            {mode === 'login' ? 'Create an account' : 'Log in'}
          </Link>
        </p>
      </div>
    </div>
  </div>;
}

function PageHeading({ eyebrow, title, body, action }: { eyebrow: string; title: string; body: string; action?: ReactNode }) {
  return <div className="mb-9 flex flex-wrap items-end justify-between gap-5 sb-enter"><div><p className="sb-mono text-[10px] uppercase tracking-[.2em] text-accent">{eyebrow}</p><h1 className="sb-display mt-3 text-4xl font-bold leading-none md:text-5xl" data-testid="text-page-title">{title}</h1><p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">{body}</p></div>{action}</div>;
}

function ScoreRing({ score, size = 'large' }: { score: number; size?: 'large' | 'small' }) {
  const radius = size === 'large' ? 44 : 28; const circumference = 2 * Math.PI * radius;
  return <div className={`relative ${size === 'large' ? 'h-28 w-28' : 'h-[72px] w-[72px]'}`}><svg className="h-full w-full -rotate-90" viewBox="0 0 110 110"><circle cx="55" cy="55" r={radius} fill="none" stroke="hsl(var(--secondary))" strokeWidth="9" /><circle cx="55" cy="55" r={radius} fill="none" stroke="hsl(var(--accent))" strokeWidth="9" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference - circumference * Math.min(score, 100) / 100} /></svg><span className={`absolute inset-0 grid place-items-center font-bold text-primary ${size === 'large' ? 'text-2xl' : 'text-base'}`} data-testid="text-score-ring">{Math.round(score)}<small className="text-[10px] font-medium">%</small></span></div>;
}

// ---------------------------------------------------------------------------
// SCREENING TEST RUNNER (FOR STUDENTS)
// ---------------------------------------------------------------------------
function ScreeningTestModal({
  testId,
  opportunityTitle,
  onClose,
  onComplete,
}: {
  testId: number;
  opportunityTitle?: string;
  onClose: () => void;
  onComplete: () => void;
}) {
  const [test, setTest] = useState<ScreeningTest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ScreeningSubmissionResult | null>(null);

  useEffect(() => {
    let active = true;
    customFetch<ScreeningTest>(`/api/screening-tests/${testId}`)
      .then((res) => { if (active) { setTest(res); setLoading(false); } })
      .catch((err) => { if (active) { setError((err as Error).message || 'Failed to load screening test'); setLoading(false); } });
    return () => { active = false; };
  }, [testId]);

  const questions = test?.questions ?? [];
  const currentQ = questions[step];

  const handleSelect = (choice: string) => {
    if (!currentQ) return;
    setAnswers({ ...answers, [String(currentQ.id)]: choice });
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    try {
      const res = await customFetch<ScreeningSubmissionResult>(`/api/screening-tests/${testId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers }),
      });
      setResult(res);
    } catch (err) {
      setError((err as Error).message || 'Failed to submit screening test');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-primary/45 p-4 backdrop-blur-sm">
      <div className="sb-card max-h-[92dvh] w-full max-w-2xl overflow-y-auto p-6 md:p-9 sb-enter relative bg-card">
        <button onClick={onClose} className="absolute right-6 top-6 text-muted-foreground hover:text-foreground" data-testid="button-close-screening-modal">
          <X size={20} />
        </button>

        {loading && <LoadingBlock label="Loading company screening test..." />}

        {error && !test && (
          <div className="py-8 text-center">
            <CircleAlert className="mx-auto text-accent mb-3" size={28} />
            <p className="text-sm font-semibold">{error}</p>
            <Button kind="ghost" onClick={onClose} className="mt-4">Close</Button>
          </div>
        )}

        {result && (
          <div className="py-6 text-center space-y-5">
            <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-secondary text-primary">
              <Award size={32} />
            </div>
            <div>
              <p className="sb-mono text-xs uppercase tracking-widest text-accent">Screening Evaluated</p>
              <h2 className="sb-display mt-2 text-3xl font-bold">
                {result.passed ? 'Screening Passed!' : 'Screening Completed'}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {result.passed
                  ? `Congratulations! You scored ${Math.round(result.score)}%, surpassing the ${result.passing_score}% requirement.`
                  : `You scored ${Math.round(result.score)}%. The passing mark was ${result.passing_score}%.`}
              </p>
            </div>

            <div className="flex justify-center py-2">
              <ScoreRing score={result.score} size="large" />
            </div>

            <div className="grid gap-3 sm:grid-cols-2 text-left max-w-md mx-auto">
              <div className="rounded-xl border border-border bg-muted/40 p-3.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                  <Sparkles size={14} className="text-accent" />
                  <span>XP Awarded</span>
                </div>
                <p className="mt-1 text-xl font-bold text-foreground">+{result.xp_awarded} XP</p>
              </div>
              <div className="rounded-xl border border-border bg-muted/40 p-3.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                  <ShieldCheck size={14} className="text-accent" />
                  <span>Company Signal</span>
                </div>
                <p className="mt-1 text-sm font-bold text-foreground">{result.passed ? 'Verified Fit' : 'Reviewed'}</p>
              </div>
            </div>

            {result.new_badges && result.new_badges.length > 0 && (
              <div className="rounded-xl border border-accent/40 bg-accent/10 p-4 text-accent text-sm font-semibold flex items-center justify-center gap-2">
                <Award size={18} />
                <span>Unlocked Badge: Screening Star! Demonstrated technical excellence.</span>
              </div>
            )}

            <div className="pt-4">
              <Button onClick={() => { onComplete(); onClose(); }} className="w-full max-w-xs mx-auto" data-testid="button-finish-screening">
                Return to Applications <ArrowRight size={15} />
              </Button>
            </div>
          </div>
        )}

        {!loading && !result && test && (
          <div>
            <div className="border-b border-border pb-4 pr-8">
              <div className="flex flex-wrap items-center gap-2">
                <span className="sb-pill bg-secondary text-primary text-xs font-bold">Screening Assessment</span>
                {opportunityTitle && <span className="text-xs text-muted-foreground">for {opportunityTitle}</span>}
              </div>
              <h2 className="sb-display mt-2 text-2xl font-bold">{test.title}</h2>
              <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><Clock size={13} /> {test.time_limit_minutes} mins</span>
                <span className="flex items-center gap-1"><Target size={13} /> {test.passing_score}% to pass</span>
                <span className="flex items-center gap-1"><HelpCircle size={13} /> {questions.length} questions</span>
              </div>
            </div>

            {questions.length > 0 ? (
              <div className="mt-6">
                <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                  <span>Question {step + 1} of {questions.length}</span>
                  <span>{Math.round(((step + 1) / questions.length) * 100)}% complete</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden mb-6">
                  <div className="h-full bg-accent transition-all duration-300" style={{ width: `${((step + 1) / questions.length) * 100}%` }} />
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-foreground leading-snug">
                    {currentQ.question_text}
                  </h3>

                  <div className="space-y-2.5 pt-2">
                    {[
                      { key: 'a', text: currentQ.option_a },
                      { key: 'b', text: currentQ.option_b },
                      { key: 'c', text: currentQ.option_c },
                      { key: 'd', text: currentQ.option_d },
                    ].map((opt) => {
                      const isSelected = answers[String(currentQ.id)] === opt.key;
                      return (
                        <button
                          key={opt.key}
                          type="button"
                          onClick={() => handleSelect(opt.key)}
                          className={`flex w-full items-center justify-between rounded-xl border p-4 text-left text-sm transition-all ${isSelected ? 'border-primary bg-secondary/80 font-semibold text-primary ring-1 ring-primary' : 'border-border bg-card hover:border-primary/40 hover:bg-muted/40'}`}
                          data-testid={`button-screening-opt-${opt.key}`}
                        >
                          <div className="flex items-center gap-3">
                            <span className={`grid h-7 w-7 place-items-center rounded-lg text-xs font-bold uppercase ${isSelected ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>
                              {opt.key}
                            </span>
                            <span>{opt.text}</span>
                          </div>
                          {isSelected && <Check size={16} className="text-primary" />}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {error && <p className="mt-4 rounded-lg bg-accent/10 p-3 text-xs text-accent">{error}</p>}

                <div className="mt-8 flex items-center justify-between border-t border-border pt-4">
                  <Button kind="ghost" disabled={step === 0} onClick={() => setStep(step - 1)}>
                    Previous
                  </Button>
                  {step < questions.length - 1 ? (
                    <Button disabled={!answers[String(currentQ.id)]} onClick={() => setStep(step + 1)} data-testid="button-next-screening-q">
                      Next Question <ArrowRight size={15} />
                    </Button>
                  ) : (
                    <Button disabled={!answers[String(currentQ.id)] || submitting} onClick={handleSubmit} data-testid="button-submit-screening">
                      {submitting ? 'Submitting…' : <>Submit Screening Test <ArrowRight size={15} /></>}
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No questions have been published for this test yet.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// INDUSTRY SCREENING TEST BUILDER MODAL
// ---------------------------------------------------------------------------
function ScreeningTestBuilderModal({
  opportunityId,
  opportunityTitle,
  onClose,
  onSaved,
}: {
  opportunityId: number;
  opportunityTitle: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [title, setTitle] = useState(`${opportunityTitle} Screening Test`);
  const [description, setDescription] = useState('Evaluate technical problem solving and core stack proficiency.');
  const [passingScore, setPassingScore] = useState(70);
  const [timeLimit, setTimeLimit] = useState(20);
  const [questions, setQuestions] = useState<Array<{
    question_text: string;
    option_a: string;
    option_b: string;
    option_c: string;
    option_d: string;
    correct_answer: string;
    explanation: string;
  }>>([
    {
      question_text: 'Which data structure offers average O(1) time complexity for lookup operations?',
      option_a: 'Binary Search Tree',
      option_b: 'Hash Map / Dictionary',
      option_c: 'Linked List',
      option_d: 'Queue',
      correct_answer: 'b',
      explanation: 'Hash maps provide O(1) average lookup using hash code distribution.',
    },
  ]);

  useEffect(() => {
    let active = true;
    customFetch<{ test: ScreeningTest | null }>(`/api/opportunities/${opportunityId}/screening-test`)
      .then((res) => {
        if (active && res.test) {
          setTitle(res.test.title);
          if (res.test.description) setDescription(res.test.description);
          setPassingScore(res.test.passing_score);
          setTimeLimit(res.test.time_limit_minutes);
          if (res.test.questions && res.test.questions.length > 0) {
            setQuestions(res.test.questions.map((q) => ({
              question_text: q.question_text,
              option_a: q.option_a,
              option_b: q.option_b,
              option_c: q.option_c,
              option_d: q.option_d,
              correct_answer: q.correct_answer || 'a',
              explanation: q.explanation || '',
            })));
          }
        }
        if (active) setLoading(false);
      })
      .catch(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [opportunityId]);

  const addQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: '',
        option_a: '',
        option_b: '',
        option_c: '',
        option_d: '',
        correct_answer: 'a',
        explanation: '',
      },
    ]);
  };

  const removeQuestion = (idx: number) => {
    setQuestions(questions.filter((_, i) => i !== idx));
  };

  const updateQuestion = (idx: number, field: string, value: string) => {
    const updated = [...questions];
    updated[idx] = { ...updated[idx], [field]: value };
    setQuestions(updated);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await customFetch(`/api/opportunities/${opportunityId}/screening-test`, {
        method: 'POST',
        body: JSON.stringify({
          title,
          description,
          passing_score: Number(passingScore),
          time_limit_minutes: Number(timeLimit),
          questions,
        }),
      });
      onSaved();
      onClose();
    } catch (err) {
      setError((err as Error).message || 'Failed to save screening test');
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-primary/45 p-4 backdrop-blur-sm">
      <div className="sb-card max-h-[92dvh] w-full max-w-3xl overflow-y-auto p-6 md:p-9 sb-enter relative bg-card">
        <div className="flex items-start justify-between border-b border-border pb-4">
          <div>
            <p className="sb-mono text-xs uppercase tracking-widest text-accent">Company Screening Builder</p>
            <h2 className="sb-display mt-1 text-2xl font-bold">{opportunityTitle}</h2>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X size={20} /></button>
        </div>

        {loading ? (
          <LoadingBlock label="Loading screening configuration..." />
        ) : (
          <form onSubmit={handleSave} className="mt-6 space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="sb-label">Test Title</label>
                <input className="sb-input" value={title} onChange={(e) => setTitle(e.target.value)} required data-testid="input-builder-title" />
              </div>
              <div className="sm:col-span-2">
                <label className="sb-label">Description / Instructions</label>
                <textarea className="sb-input min-h-20" value={description} onChange={(e) => setDescription(e.target.value)} required />
              </div>
              <div>
                <label className="sb-label">Passing Score (%)</label>
                <input type="number" min={10} max={100} className="sb-input" value={passingScore} onChange={(e) => setPassingScore(Number(e.target.value))} required />
              </div>
              <div>
                <label className="sb-label">Time Limit (Minutes)</label>
                <input type="number" min={5} max={180} className="sb-input" value={timeLimit} onChange={(e) => setTimeLimit(Number(e.target.value))} required />
              </div>
            </div>

            <div className="border-t border-border pt-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-bold text-foreground">Screening Questions ({questions.length})</h3>
                  <p className="text-xs text-muted-foreground">Multiple-choice questions candidate must answer to demonstrate ability.</p>
                </div>
                <Button type="button" kind="ghost" onClick={addQuestion} className="text-xs py-1.5 px-3">
                  <Plus size={14} /> Add Question
                </Button>
              </div>

              <div className="space-y-6">
                {questions.map((q, qIndex) => (
                  <div key={qIndex} className="rounded-xl border border-border bg-muted/30 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-accent">Question {qIndex + 1}</span>
                      {questions.length > 1 && (
                        <button type="button" onClick={() => removeQuestion(qIndex)} className="text-muted-foreground hover:text-accent">
                          <Trash2 size={15} />
                        </button>
                      )}
                    </div>
                    <input
                      className="sb-input bg-card font-medium"
                      placeholder="Enter question text here..."
                      value={q.question_text}
                      onChange={(e) => updateQuestion(qIndex, 'question_text', e.target.value)}
                      required
                    />

                    <div className="grid gap-2 sm:grid-cols-2 pt-1">
                      {(['a', 'b', 'c', 'd'] as const).map((key) => (
                        <div key={key} className="flex items-center gap-2">
                          <label className="flex items-center gap-1.5 cursor-pointer text-xs font-semibold uppercase">
                            <input
                              type="radio"
                              name={`correct_${qIndex}`}
                              checked={q.correct_answer === key}
                              onChange={() => updateQuestion(qIndex, 'correct_answer', key)}
                            />
                            {key.toUpperCase()}
                          </label>
                          <input
                            className="sb-input bg-card text-xs py-1.5"
                            placeholder={`Option ${key.toUpperCase()}`}
                            value={q[`option_${key}` as keyof typeof q]}
                            onChange={(e) => updateQuestion(qIndex, `option_${key}`, e.target.value)}
                            required
                          />
                        </div>
                      ))}
                    </div>

                    <div>
                      <input
                        className="sb-input bg-card text-xs py-1.5"
                        placeholder="Explanation (shown to reviewer / scoring notes)"
                        value={q.explanation}
                        onChange={(e) => updateQuestion(qIndex, 'explanation', e.target.value)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {error && <p className="rounded-lg bg-accent/10 p-3 text-xs text-accent">{error}</p>}

            <div className="flex justify-end gap-3 border-t border-border pt-4">
              <Button type="button" kind="ghost" onClick={onClose}>Cancel</Button>
              <Button type="submit" disabled={saving || !questions.length} data-testid="button-save-screening">
                {saving ? 'Saving…' : 'Save Screening Test'}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// STUDENT DASHBOARD
// ---------------------------------------------------------------------------
function StudentDashboard({ user }: { user?: User }) {
  const profile = useGetStudentProfile(); const gaps = useGetStudentSkillGaps(); const applications = useGetStudentApplications(); const opportunities = useListOpportunities();
  const [activeScreeningTestId, setActiveScreeningTestId] = useState<number | null>(null);
  const [activeScreeningTitle, setActiveScreeningTitle] = useState<string | undefined>();
  const client = useQueryClient();

  const loading = profile.isLoading || gaps.isLoading || applications.isLoading || opportunities.isLoading;
  const anyError = profile.isError || gaps.isError || applications.isError || opportunities.isError;
  if (loading) return <><PageHeading eyebrow="Student workspace" title="Your readiness, in view." body="Loading your evidence and the opportunities that fit it." /><LoadingBlock label="Gathering your readiness signals" /></>;
  if (anyError) return <><PageHeading eyebrow="Student workspace" title="Your readiness, in view." body="We hit a temporary signal gap." /><ErrorBlock onRetry={() => { profile.refetch(); gaps.refetch(); applications.refetch(); opportunities.refetch(); }} /></>;
  const data = profile.data; const gapData = gaps.data; const appData = applications.data ?? data?.applications ?? []; const oppData = opportunities.data ?? [];
  if (!data) return <EmptyBlock title="Your profile is taking shape" text="Complete your first assessment to see your readiness signal here." action={<Link className="sb-btn sb-btn-primary" href="/assessment" data-testid="link-dashboard-assessment">Take assessment <ArrowRight size={15} /></Link>} />;
  const score = gapData?.overall_readiness ?? data.overall_readiness ?? 0;

  return <>
    <PageHeading
      eyebrow={`Good to see you, ${user?.name?.split(' ')[0] ?? data.name}`}
      title="Your readiness, in view."
      body="A focused picture of what you can bring now — and what to build next."
      action={
        <div className="flex flex-wrap items-center gap-3">
          {(data.age || data.gender) && (
            <span className="sb-pill bg-muted text-muted-foreground text-xs font-semibold">
              {data.age ? `${data.age} yrs` : ''}{data.age && data.gender ? ' · ' : ''}{data.gender ?? ''}
            </span>
          )}
          {!data.has_taken_assessment && (
            <Link href="/assessment" className="sb-btn sb-btn-primary" data-testid="link-take-assessment">
              <ClipboardCheck size={16} /> Take assessment
            </Link>
          )}
        </div>
      }
    />

    <div className="grid gap-5 lg:grid-cols-[1.08fr_.92fr]">
      <section className="sb-card relative overflow-hidden bg-primary p-7 text-primary-foreground md:p-9">
        <div className="relative z-10 flex flex-wrap items-center justify-between gap-8">
          <div>
            <p className="sb-mono text-[10px] uppercase tracking-[.18em] text-primary-foreground/55">Overall readiness</p>
            <h2 className="sb-display mt-3 text-5xl font-bold">{Math.round(score)}<span className="text-2xl text-secondary">%</span></h2>
            <p className="mt-3 max-w-xs text-sm leading-6 text-primary-foreground/65">{data.has_taken_assessment ? 'A living signal based on your latest assessment.' : 'One assessment away from your first signal.'}</p>
          </div>
          <ScoreRing score={score} />
        </div>
        <div className="relative z-10 mt-9 border-t border-primary-foreground/15 pt-4 text-xs text-primary-foreground/60">
          <span className="text-secondary">Next useful move:</span> {score < 70 ? 'strengthen your top gap with a targeted practice.' : 'apply where your strongest signals can travel.'}
        </div>
        <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full border-[38px] border-secondary/10" />
      </section>
      <section className="sb-card p-7 md:p-9">
        <div className="flex items-start justify-between">
          <div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Skill profile</p><h2 className="sb-display mt-2 text-2xl font-bold">Your signal set</h2></div>
          <Target className="text-accent" size={21} />
        </div>
        <div className="mt-7 space-y-4">
          {(data.skills ?? []).length ? data.skills.slice(0, 5).map((skill) => <SkillBar key={skill.skill_id} name={skill.skill_name} score={skill.score} />) : <p className="text-sm text-muted-foreground">Take the assessment to map your skills.</p>}
        </div>
      </section>
    </div>

    <div className="mt-5 grid gap-5 lg:grid-cols-[.92fr_1.08fr]">
      <section className="sb-card p-7 md:p-8">
        <div className="flex items-start justify-between">
          <div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Build next</p><h2 className="sb-display mt-2 text-2xl font-bold">Your skill gaps</h2></div>
          <Link href="/assessment" className="text-sm font-bold text-primary" data-testid="link-review-gaps">Review <ArrowRight className="ml-1 inline" size={14} /></Link>
        </div>
        <div className="mt-6 space-y-3">
          {(gapData?.skill_gaps ?? data.skill_gaps ?? []).slice(0, 4).map((gap) => <GapRow gap={gap} key={gap.skill_id} />)}
        </div>
        {!(gapData?.skill_gaps ?? data.skill_gaps ?? []).length && <p className="mt-5 text-sm text-muted-foreground">No gaps yet. Your first assessment will make the next step clearer.</p>}
      </section>

      <section className="sb-card p-7 md:p-8">
        <div className="flex items-start justify-between">
          <div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Matched for you</p><h2 className="sb-display mt-2 text-2xl font-bold">Recommended opportunities</h2></div>
          <BriefcaseBusiness className="text-accent" size={21} />
        </div>
        <div className="mt-6 space-y-3">
          {oppData.slice(0, 3).map((opp) => <OpportunityRow opportunity={opp} key={opp.id} />)}
          {!oppData.length && <EmptyBlock title="The board is quiet" text="New opportunities will appear here as teams post roles." />}
        </div>
      </section>
    </div>

    <section className="sb-card mt-5 p-7 md:p-8">
      <div className="flex items-start justify-between">
        <div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Your movement</p><h2 className="sb-display mt-2 text-2xl font-bold">Applications & Screenings</h2></div>
        <Send className="text-accent" size={21} />
      </div>
      {appData.length ? (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="pb-3 font-medium">Opportunity</th>
                <th className="pb-3 font-medium">Company</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Screening Test</th>
                <th className="pb-3 text-right font-medium">Applied</th>
              </tr>
            </thead>
            <tbody>
              {appData.map((app) => (
                <tr key={app.id} className="border-b border-border/70 last:border-0" data-testid={`row-application-${app.id}`}>
                  <td className="py-4 font-semibold">{app.title ?? `Opportunity #${app.opportunity_id}`}</td>
                  <td className="py-4 text-muted-foreground">{app.company_name ?? '—'}</td>
                  <td className="py-4"><StatusPill status={app.status} /></td>
                  <td className="py-4">
                    {app.screening ? (
                      <span className={`sb-pill ${app.screening.passed ? 'bg-emerald-500/10 text-emerald-600 font-semibold' : 'bg-accent/10 text-accent font-semibold'}`}>
                        {Math.round(app.screening.score)}% {app.screening.passed ? '✓ Passed' : '✗ Retake'}
                      </span>
                    ) : app.screening_test_id ? (
                      <button
                        type="button"
                        onClick={() => { setActiveScreeningTestId(app.screening_test_id!); setActiveScreeningTitle(app.title); }}
                        className="sb-btn sb-btn-sun py-1 px-3 text-xs inline-flex items-center gap-1 font-semibold"
                        data-testid={`button-take-screening-${app.id}`}
                      >
                        <ClipboardCheck size={13} /> Take Screening Test
                      </button>
                    ) : (
                      <span className="text-xs text-muted-foreground">Not Required</span>
                    )}
                  </td>
                  <td className="py-4 text-right text-muted-foreground">{app.applied_at ? new Date(app.applied_at).toLocaleDateString() : 'Recently'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-5">
          <EmptyBlock title="No applications yet" text="When you find a good fit, your progress and company screening tests will live here." action={<Link href="/student" className="sb-btn sb-btn-sun" data-testid="link-browse-opportunities">Browse recommendations</Link>} />
        </div>
      )}
    </section>

    {activeScreeningTestId !== null && (
      <ScreeningTestModal
        testId={activeScreeningTestId}
        opportunityTitle={activeScreeningTitle}
        onClose={() => setActiveScreeningTestId(null)}
        onComplete={() => {
          client.invalidateQueries({ queryKey: getGetStudentApplicationsQueryKey() });
          client.invalidateQueries({ queryKey: getGetStudentProfileQueryKey() });
        }}
      />
    )}
  </>;
}

function SkillBar({ name, score }: { name: string; score: number }) { return <div><div className="mb-2 flex justify-between text-sm"><span className="font-medium">{name}</span><span className="sb-mono text-xs text-muted-foreground">{Math.round(score)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-secondary"><div className="sb-progress h-full rounded-full bg-primary" style={{ width: `${Math.min(score, 100)}%` }} /></div></div>; }
function GapRow({ gap }: { gap: SkillGap }) { return <div className="flex items-center gap-3 rounded-lg bg-muted/60 px-3 py-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-card text-xs font-bold text-accent">{Math.round(gap.score)}</span><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{gap.skill_name}</p><p className="text-xs text-muted-foreground">{gap.improvement}</p></div><StatusPill status={gap.status} /></div>; }
function StatusPill({ status }: { status: string }) { const positive = ['accepted', 'shortlisted', 'Strong'].includes(status); const warm = ['Developing', 'applied'].includes(status); return <span className={`sb-pill ${positive ? 'bg-primary/10 text-primary' : warm ? 'bg-secondary text-primary' : 'bg-accent/10 text-accent'}`} data-testid={`status-${status.replaceAll(' ', '-').toLowerCase()}`}>{status}</span>; }
function OpportunityRow({ opportunity }: { opportunity: OpportunityWithMatch }) { return <Link href={`/opportunity/${opportunity.id}`} className="sb-card sb-card-lift flex items-center gap-4 p-4" data-testid={`card-opportunity-${opportunity.id}`}><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-secondary text-primary"><BriefcaseBusiness size={18} /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-bold">{opportunity.title}</p><p className="mt-1 text-xs text-muted-foreground">{opportunity.company_name}</p></div><div className="text-right"><span className="sb-mono text-sm font-bold text-primary">{Math.round(opportunity.match_percentage)}%</span><p className="text-[10px] text-muted-foreground">match</p></div><ChevronRight size={16} className="text-muted-foreground" /></Link>; }

function AssessmentPage() {
  const assessment = useGetAssessment(); const submit = useSubmitAssessment(); const client = useQueryClient(); const [, navigate] = useLocation();
  const [step, setStep] = useState(0); const [answers, setAnswers] = useState<Record<string, number>>({}); const [result, setResult] = useState<{ message: string; skills: { skill_name: string; score: number }[] } | null>(null); const [error, setError] = useState('');
  const questions = assessment.data ?? []; const question = questions[step];
  const select = (index: number) => setAnswers({ ...answers, [String(question.id)]: index });
  const finish = () => submit.mutate({ data: { answers } }, { onSuccess: (data) => { setResult(data); client.invalidateQueries({ queryKey: getGetStudentProfileQueryKey() }); client.invalidateQueries({ queryKey: getGetStudentSkillGapsQueryKey() }); client.invalidateQueries({ queryKey: getListOpportunitiesQueryKey() }); }, onError: (err) => setError((err as Error).message) });
  if (assessment.isLoading) return <><PageHeading eyebrow="Skill assessment" title="Find your signal." body="Twelve focused questions, then a clearer next step." /><LoadingBlock label="Preparing your assessment" /></>;
  if (assessment.isError) return <><PageHeading eyebrow="Skill assessment" title="Find your signal." body="The assessment could not load." /><ErrorBlock onRetry={() => assessment.refetch()} /></>;
  if (result) return <div className="mx-auto max-w-3xl sb-enter"><div className="sb-card overflow-hidden"><div className="bg-primary p-9 text-primary-foreground md:p-12"><span className="sb-pill bg-secondary text-primary">Signal captured</span><h1 className="sb-display mt-5 text-4xl font-bold md:text-5xl">Now you have somewhere to go.</h1><p className="mt-4 max-w-xl leading-7 text-primary-foreground/70">{result.message}</p></div><div className="p-7 md:p-10"><div className="grid gap-5 sm:grid-cols-2">{result.skills.map((skill) => <div key={skill.skill_name} className="flex items-center justify-between rounded-xl bg-muted/60 p-4"><div><p className="font-semibold">{skill.skill_name}</p><p className="mt-1 text-xs text-muted-foreground">Current signal</p></div><ScoreRing score={skill.score} size="small" /></div>)}</div><div className="mt-8 flex flex-wrap gap-3"><Button onClick={() => navigate('/student')} data-testid="button-see-readiness">See my readiness <ArrowRight size={15} /></Button><Button kind="ghost" onClick={() => { setResult(null); setAnswers({}); setStep(0); }} data-testid="button-retake-assessment">Retake assessment</Button></div></div></div></div>;
  if (!questions.length) return <EmptyBlock title="Assessment unavailable" text="There are no questions ready yet. Please check back shortly." />;
  return <div className="mx-auto max-w-3xl sb-enter"><div className="mb-8 flex items-center justify-between"><div><p className="sb-mono text-[10px] uppercase tracking-[.2em] text-accent">Skill assessment</p><h1 className="sb-display mt-3 text-4xl font-bold">Find your signal.</h1></div><span className="sb-mono text-xs text-muted-foreground" data-testid="text-assessment-progress">{String(step + 1).padStart(2, '0')} / {String(questions.length).padStart(2, '0')}</span></div><div className="mb-8 h-1.5 overflow-hidden rounded-full bg-secondary"><div className="sb-progress h-full rounded-full bg-accent" style={{ width: `${((step + 1) / questions.length) * 100}%` }} /></div><div className="sb-card p-7 md:p-12"><span className="sb-pill bg-secondary text-primary">{question.skill}</span><h2 className="sb-display mt-7 text-3xl font-bold leading-tight md:text-4xl" data-testid={`text-question-${question.id}`}>{question.question}</h2><div className="mt-9 space-y-3">{question.options.map((option, index) => <button key={option} onClick={() => select(index)} className={`flex w-full items-center justify-between rounded-xl border px-4 py-4 text-left text-sm transition-all ${answers[String(question.id)] === index ? 'border-primary bg-secondary font-semibold text-primary' : 'border-border bg-card hover:border-primary/40 hover:bg-muted'}`} data-testid={`button-answer-${question.id}-${index}`}><span>{option}</span>{answers[String(question.id)] === index && <Check size={17} />}</button>)}</div>{error && <p className="mt-4 rounded-lg bg-accent/10 p-3 text-sm text-accent" data-testid="status-assessment-error">{error}</p>}<div className="mt-9 flex justify-between"><Button kind="ghost" onClick={() => setStep(Math.max(step - 1, 0))} disabled={step === 0} data-testid="button-previous-question">Previous</Button>{step === questions.length - 1 ? <Button onClick={finish} disabled={answers[String(question.id)] === undefined || submit.isPending} data-testid="button-submit-assessment">{submit.isPending ? 'Scoring…' : 'Submit assessment'} <ArrowRight size={15} /></Button> : <Button onClick={() => setStep(step + 1)} disabled={answers[String(question.id)] === undefined} data-testid="button-next-question">Next question <ArrowRight size={15} /></Button>}</div></div></div>;
}

function IndustryPage() {
  const skills = useListSkills(); const mine = useListMyOpportunities(); const client = useQueryClient(); const create = useCreateOpportunity(); const update = useUpdateApplicationStatus();
  const [showCreate, setShowCreate] = useState(false); const [selectedId, setSelectedId] = useState<number | null>(null); const [title, setTitle] = useState(''); const [company, setCompany] = useState(''); const [description, setDescription] = useState(''); const [skillIds, setSkillIds] = useState<number[]>([]); const [error, setError] = useState('');
  const [screeningBuilderOpp, setScreeningBuilderOpp] = useState<{ id: number; title: string } | null>(null);

  const applicants = useListOpportunityApplicants(selectedId ?? 0, { query: { enabled: selectedId !== null, queryKey: getListOpportunityApplicantsQueryKey(selectedId ?? 0) } });
  const selected = mine.data?.find((x) => x.id === selectedId);
  const submit = (e: FormEvent) => { e.preventDefault(); setError(''); create.mutate({ data: { title, company_name: company, description, required_skills: skillIds.map((id) => ({ skill_id: id, required_score: 65 })) } }, { onSuccess: () => { setShowCreate(false); setTitle(''); setCompany(''); setDescription(''); setSkillIds([]); client.invalidateQueries({ queryKey: getListMyOpportunitiesQueryKey() }); client.invalidateQueries({ queryKey: getListOpportunitiesQueryKey() }); }, onError: (err) => setError((err as Error).message) }); };
  const changeStatus = (applicationId: number, status: 'shortlisted' | 'rejected' | 'accepted') => update.mutate({ applicationId, data: { status } }, { onSuccess: () => client.invalidateQueries({ queryKey: getListOpportunityApplicantsQueryKey(selectedId ?? 0) }) });
  if (mine.isLoading || skills.isLoading) return <><PageHeading eyebrow="Industry workspace" title="Make a fairer call." body="Create opportunities and meet candidates through transparent skill signals." /><LoadingBlock label="Loading your opportunity desk" /></>;
  if (mine.isError || skills.isError) return <ErrorBlock onRetry={() => { mine.refetch(); skills.refetch(); }} />;
  return <><PageHeading eyebrow="Industry workspace" title="Make a fairer call." body="Create opportunities and meet candidates through transparent skill signals." action={<Button onClick={() => setShowCreate(true)} data-testid="button-create-opportunity"><Plus size={17} /> Post opportunity</Button>} /><div className="grid gap-5 lg:grid-cols-[.8fr_1.2fr]"><section className="sb-card bg-secondary p-7 md:p-8"><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-primary/55">Decision principle</p><h2 className="sb-display mt-4 text-3xl font-bold leading-tight">Start with what the work asks for.</h2><p className="mt-4 text-sm leading-6 text-primary/70">Skill matches and custom screening tests make the first conversation more useful — not less human.</p><div className="mt-8 flex items-center gap-3 text-sm font-semibold text-primary"><ShieldCheck size={17} /> Skill-based by design</div></section><section className="sb-card p-7 md:p-8"><div className="flex items-start justify-between"><div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Your desk</p><h2 className="sb-display mt-2 text-2xl font-bold">Posted opportunities</h2></div><span className="sb-pill bg-muted text-muted-foreground">{mine.data?.length ?? 0} live</span></div><div className="mt-6 space-y-3">{mine.data?.map((opp) => <div key={opp.id} className={`flex w-full items-center justify-between gap-4 rounded-xl border p-4 transition-colors ${selectedId === opp.id ? 'border-primary bg-secondary' : 'border-border bg-card hover:border-primary/40'}`} data-testid={`button-opportunity-${opp.id}`}><button type="button" onClick={() => setSelectedId(opp.id)} className="flex items-center gap-4 min-w-0 flex-1 text-left"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground"><BriefcaseBusiness size={18} /></div><div className="min-w-0 flex-1"><p className="truncate font-semibold">{opp.title}</p><p className="mt-1 text-xs text-muted-foreground">{opp.company_name} · {opp.required_skills?.length ?? 0} skills</p></div></button><div className="flex items-center gap-2"><button type="button" onClick={() => setScreeningBuilderOpp({ id: opp.id, title: opp.title })} className="rounded-lg border border-border bg-card px-2.5 py-1 text-xs font-semibold text-primary hover:border-primary/50 hover:bg-secondary flex items-center gap-1" data-testid={`button-screening-config-${opp.id}`}><Settings size={12} /> Screening Test</button><button type="button" onClick={() => setSelectedId(opp.id)} className="text-muted-foreground hover:text-foreground"><ChevronRight size={16} /></button></div></div>)}{!mine.data?.length && <EmptyBlock title="Your opportunity desk is clear" text="Post a role to start seeing skill-based applicants." action={<Button onClick={() => setShowCreate(true)} kind="sun" data-testid="button-empty-create">Post first opportunity</Button>} />}</div></section></div>{selectedId && <section className="sb-card mt-5 p-7 md:p-8 sb-enter"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-accent">Applicant signal</p><h2 className="sb-display mt-2 text-3xl font-bold">{selected?.title}</h2><p className="mt-2 text-sm text-muted-foreground">{selected?.description}</p></div><div className="flex items-center gap-3"><Button kind="sun" onClick={() => setScreeningBuilderOpp({ id: selectedId, title: selected?.title || '' })} className="text-xs py-1.5 px-3"><Settings size={14} /> Configure Screening Test</Button><Button kind="ghost" onClick={() => setSelectedId(null)} data-testid="button-close-applicants"><X size={15} /> Close</Button></div></div>{applicants.isLoading ? <div className="mt-6"><LoadingBlock label="Loading applicant signals" /></div> : applicants.isError ? <div className="mt-6"><ErrorBlock onRetry={() => applicants.refetch()} /></div> : applicants.data?.applicants?.length ? <div className="mt-7 space-y-3">{applicants.data.applicants.map((app) => <ApplicantRow applicant={app} key={app.application_id} onStatus={(status) => changeStatus(app.application_id, status)} />)}</div> : <div className="mt-6"><EmptyBlock title="No applicants yet" text="When students apply, their skill signal will appear here." /></div>}</section>}{showCreate && <div className="fixed inset-0 z-40 grid place-items-center bg-primary/35 p-5 backdrop-blur-sm"><div className="sb-card max-h-[90dvh] w-full max-w-xl overflow-y-auto p-7 md:p-9 sb-enter"><div className="flex items-start justify-between"><div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-accent">New opportunity</p><h2 className="sb-display mt-2 text-3xl font-bold">Make the ask clear.</h2></div><button onClick={() => setShowCreate(false)} data-testid="button-close-create"><X size={19} /></button></div><form onSubmit={submit} className="mt-7 space-y-5"><div><label className="sb-label">Opportunity title</label><input className="sb-input" value={title} onChange={(e) => setTitle(e.target.value)} required data-testid="input-opportunity-title" /></div><div><label className="sb-label">Company name</label><input className="sb-input" value={company} onChange={(e) => setCompany(e.target.value)} required data-testid="input-company-name" /></div><div><label className="sb-label">Description</label><textarea className="sb-input min-h-28 resize-y" value={description} onChange={(e) => setDescription(e.target.value)} required data-testid="input-opportunity-description" /></div><div><label className="sb-label">Required skills · select at least one</label><div className="grid grid-cols-2 gap-2">{(skills.data ?? []).map((skill) => <button type="button" key={skill.id} onClick={() => setSkillIds(skillIds.includes(skill.id) ? skillIds.filter((id) => id !== skill.id) : [...skillIds, skill.id])} className={`rounded-lg border px-3 py-3 text-left text-sm ${skillIds.includes(skill.id) ? 'border-primary bg-secondary font-semibold text-primary' : 'border-border bg-card text-muted-foreground'}`} data-testid={`button-skill-${skill.id}`}>{skill.name}{skillIds.includes(skill.id) && <Check className="float-right" size={15} />}</button>)}</div></div>{error && <p className="rounded-lg bg-accent/10 p-3 text-sm text-accent">{error}</p>}<div className="flex justify-end gap-3"><Button type="button" kind="ghost" onClick={() => setShowCreate(false)} data-testid="button-cancel-create">Cancel</Button><Button type="submit" disabled={create.isPending || !skillIds.length} data-testid="button-submit-opportunity">{create.isPending ? 'Posting…' : 'Post opportunity'} <ArrowRight size={15} /></Button></div></form></div></div>}
    {screeningBuilderOpp && (
      <ScreeningTestBuilderModal
        opportunityId={screeningBuilderOpp.id}
        opportunityTitle={screeningBuilderOpp.title}
        onClose={() => setScreeningBuilderOpp(null)}
        onSaved={() => {
          client.invalidateQueries({ queryKey: getListMyOpportunitiesQueryKey() });
          client.invalidateQueries({ queryKey: getListOpportunityApplicantsQueryKey(selectedId ?? 0) });
        }}
      />
    )}
  </>;
}

function ApplicantRow({ applicant, onStatus }: { applicant: Applicant; onStatus: (status: 'shortlisted' | 'rejected' | 'accepted') => void }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-center gap-4">
        <div className="grid h-10 w-10 place-items-center rounded-full bg-secondary text-sm font-bold text-primary">
          {applicant.name.split(' ').map((x) => x[0]).join('').slice(0, 2)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="font-semibold text-foreground">{applicant.name}</p>
            {(applicant.age || applicant.gender) && (
              <span className="text-xs text-muted-foreground">
                ({applicant.age ? `${applicant.age}y` : ''}{applicant.age && applicant.gender ? ' · ' : ''}{applicant.gender ?? ''})
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">{applicant.email}</p>
        </div>
        {applicant.screening ? (
          <span className={`sb-pill ${applicant.screening.passed ? 'bg-emerald-500/10 text-emerald-600 font-bold' : 'bg-accent/10 text-accent font-bold'}`} data-testid={`screening-status-${applicant.application_id}`}>
            Screening: {Math.round(applicant.screening.score)}% ({applicant.screening.passed ? 'Passed' : 'Failed'})
          </span>
        ) : (
          <span className="sb-pill bg-muted text-muted-foreground text-xs" data-testid={`screening-pending-${applicant.application_id}`}>
            Screening: Pending
          </span>
        )}
        <ScoreRing score={applicant.match_percentage} size="small" />
        <StatusPill status={applicant.status} />
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-3">
        {applicant.skill_matches?.slice(0, 4).map((skill) => (
          <span className="sb-pill bg-muted text-muted-foreground" key={skill.skill_name}>
            {skill.skill_name} {Math.round(skill.match_score)}%
          </span>
        ))}
        <div className="ml-auto flex gap-2">
          <button onClick={() => onStatus('shortlisted')} className="rounded-md px-2 py-1 text-xs font-bold text-primary hover:bg-secondary" data-testid={`button-shortlist-${applicant.application_id}`}>
            Shortlist
          </button>
          <button onClick={() => onStatus('rejected')} className="rounded-md px-2 py-1 text-xs font-bold text-accent hover:bg-accent/10" data-testid={`button-reject-${applicant.application_id}`}>
            Reject
          </button>
        </div>
      </div>
    </div>
  );
}

function InstitutionPage() {
  const stats = useGetInstitutionStats();
  if (stats.isLoading) return <><PageHeading eyebrow="Institution view" title="Readiness, responsibly." body="A clear aggregate view for better curriculum and career conversations." /><LoadingBlock label="Compiling institution signals" /></>;
  if (stats.isError) return <ErrorBlock onRetry={() => stats.refetch()} />;
  const data = stats.data as InstitutionStats | undefined;
  if (!data) return <EmptyBlock title="No aggregate signal yet" text="Once students complete assessments, this view will show your institution's readiness picture." />;
  return <><PageHeading eyebrow="Institution view" title="Readiness, responsibly." body="See the aggregate signal without exposing private student data." /><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><StatCard label="Students" value={data.student_count} icon={Users} /><StatCard label="Assessed" value={data.assessed_student_count} icon={ClipboardCheck} /><StatCard label="Overall readiness" value={`${Math.round(data.overall_readiness)}%`} icon={TrendingUp} /><StatCard label="Assessment coverage" value={`${data.student_count ? Math.round(data.assessed_student_count / data.student_count * 100) : 0}%`} icon={ShieldCheck} /></div><div className="mt-5 grid gap-5 lg:grid-cols-[1.25fr_.75fr]"><section className="sb-card p-7 md:p-9"><div className="flex items-start justify-between"><div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Skill landscape</p><h2 className="sb-display mt-2 text-2xl font-bold">Where the cohort stands</h2></div><BarChart3 className="text-accent" size={21} /></div><div className="mt-7 space-y-6">{(data.skills ?? []).map((skill) => <div key={skill.skill_name}><div className="mb-2 flex items-center justify-between gap-3"><span className="font-semibold">{skill.skill_name}</span><span className="sb-mono text-xs text-muted-foreground">{Math.round(skill.average_score)}% average · {skill.needs_improvement} need support</span></div><div className="h-3 overflow-hidden rounded-full bg-secondary"><div className="sb-progress h-full rounded-full bg-primary" style={{ width: `${Math.min(skill.average_score, 100)}%` }} /></div></div>)}{!data.skills?.length && <p className="text-sm text-muted-foreground">No skill breakdown is available yet.</p>}</div></section><section className="sb-card p-7 md:p-9"><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Signal notes</p><div className="mt-7 space-y-5"><div className="rounded-xl bg-secondary p-4"><p className="text-xs font-bold uppercase tracking-wider text-primary/60">Strongest skill</p><p className="mt-2 text-lg font-bold">{data.strongest_skill?.skill_name ?? 'Not enough data'}</p><p className="mt-1 text-sm text-primary/65">{data.strongest_skill ? `${Math.round(data.strongest_skill.average_score)}% cohort average` : 'Keep building the assessment sample.'}</p></div><div className="rounded-xl bg-accent/10 p-4"><p className="text-xs font-bold uppercase tracking-wider text-accent/70">Common gap</p><p className="mt-2 text-lg font-bold">{data.common_skill_gap?.skill_name ?? 'Not enough data'}</p><p className="mt-1 text-sm text-accent/75">{data.common_skill_gap ? `${data.common_skill_gap.needs_improvement} students need support` : 'No gap signal yet.'}</p></div><div className="flex gap-3 pt-2 text-sm leading-6 text-muted-foreground"><ShieldCheck className="mt-1 shrink-0 text-primary" size={17} /><span>This view is aggregate by design. Individual student scores stay in their own workspace.</span></div></div></section></div></>;
}

function StatCard({ label, value, icon: Icon }: { label: string; value: string | number; icon: typeof Users }) { return <div className="sb-card p-5"><Icon className="mb-6 text-accent" size={19} /><p className="sb-mono text-[10px] uppercase tracking-[.16em] text-muted-foreground">{label}</p><p className="sb-display mt-2 text-3xl font-bold" data-testid={`text-stat-${label.toLowerCase().replaceAll(' ', '-')}`}>{value}</p></div>; }

function OpportunityDetail({ user }: { user?: User }) {
  const [, params] = useRoute('/opportunity/:id'); const id = Number(params?.id ?? 0); const opp = useGetOpportunity(id, { query: { queryKey: [`/api/opportunities/${id}`], enabled: Boolean(id) } }); const apply = useApplyToOpportunity(); const client = useQueryClient(); const [message, setMessage] = useState('');
  const [screeningTest, setScreeningTest] = useState<ScreeningTest | null>(null);
  const [showScreeningModal, setShowScreeningModal] = useState(false);

  useEffect(() => {
    if (!id) return;
    customFetch<{ test: ScreeningTest | null }>(`/api/opportunities/${id}/screening-test`)
      .then((res) => { if (res.test) setScreeningTest(res.test); })
      .catch(() => {});
  }, [id]);

  if (opp.isLoading) return <LoadingBlock label="Loading opportunity signal" />;
  if (opp.isError || !opp.data) return <ErrorBlock />;
  const data = opp.data;
  return <div className="mx-auto max-w-4xl sb-enter"><Link href={user?.role === 'industry' ? '/industry' : '/student'} className="mb-7 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground" data-testid="link-back-opportunities"><ChevronRight className="rotate-180" size={15} /> Back to opportunities</Link><div className="sb-card overflow-hidden"><div className="bg-primary p-8 text-primary-foreground md:p-12"><div className="flex flex-wrap items-start justify-between gap-7"><div><span className="sb-pill bg-secondary text-primary">{data.company_name}</span><h1 className="sb-display mt-5 text-4xl font-bold leading-tight md:text-5xl">{data.title}</h1><p className="mt-3 text-sm text-primary-foreground/65">{data.opportunity_type}</p></div><div className="text-center"><ScoreRing score={data.match_percentage} /><p className="mt-2 text-xs text-primary-foreground/60">your match</p></div></div></div><div className="p-8 md:p-12"><div className="grid gap-10 md:grid-cols-[1fr_.8fr]"><div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">The opportunity</p><p className="mt-4 leading-8 text-muted-foreground">{data.description}</p><div className="mt-8 flex flex-wrap gap-2">{data.required_skills?.map((skill) => <span className="sb-pill bg-muted text-muted-foreground" key={skill.skill_id}>{skill.skill_name} · {skill.required_score}%</span>)}</div></div><div><p className="sb-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">Your skill match</p><div className="mt-4 space-y-3">{data.skill_matches?.map((skill) => <div className="flex items-center justify-between border-b border-border pb-3 text-sm" key={skill.skill_name}><span>{skill.skill_name}</span><span className={skill.status === 'Strong' ? 'font-bold text-primary' : 'text-muted-foreground'}>{Math.round(skill.current_score)} / {Math.round(skill.required_score)}</span></div>)}</div></div></div>

  {screeningTest && (
    <div className="mt-8 rounded-xl border border-secondary bg-secondary/30 p-5 flex flex-wrap items-center justify-between gap-4">
      <div>
        <div className="flex items-center gap-2 text-primary font-bold text-sm">
          <Award size={16} />
          <span>Company Screening Test Included</span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{screeningTest.title} · {screeningTest.questions.length} questions · {screeningTest.passing_score}% passing threshold</p>
      </div>
      {user?.role === 'student' && (
        <Button kind="sun" onClick={() => setShowScreeningModal(true)} className="text-xs py-1.5 px-3.5">
          Take Screening Test
        </Button>
      )}
    </div>
  )}

  {message && <p className="mt-8 rounded-lg bg-secondary p-3 text-sm font-semibold text-primary" data-testid="status-apply-success">{message}</p>}
  {user?.role === 'student' && <Button className="mt-9" onClick={() => apply.mutate({ opportunityId: id }, { onSuccess: (data) => { setMessage(data.message); client.invalidateQueries({ queryKey: getGetStudentApplicationsQueryKey() }); }, onError: (err) => setMessage((err as Error).message) })} disabled={apply.isPending} data-testid="button-apply-opportunity">{apply.isPending ? 'Sending application…' : 'Apply to this opportunity'} <Send size={15} /></Button>}</div></div>

  {showScreeningModal && screeningTest && (
    <ScreeningTestModal
      testId={screeningTest.id}
      opportunityTitle={data.title}
      onClose={() => setShowScreeningModal(false)}
      onComplete={() => {
        client.invalidateQueries({ queryKey: getGetStudentApplicationsQueryKey() });
        client.invalidateQueries({ queryKey: getGetStudentProfileQueryKey() });
      }}
    />
  )}
</div>;
}

function Router({ user, onAuth, onLogout }: { user?: User; onAuth: (user: User, token?: string) => void; onLogout: () => void }) {
  return <Switch><Route path="/" component={Landing} /><Route path="/login">{() => <Auth mode="login" onAuth={onAuth} />}</Route><Route path="/register">{() => <Auth mode="register" onAuth={onAuth} />}</Route><Route path="/student">{() => <AppShell user={user} onLogout={onLogout}><StudentDashboard user={user} /></AppShell>}</Route><Route path="/assessment">{() => <AppShell user={user} onLogout={onLogout}><AssessmentPage /></AppShell>}</Route><Route path="/industry">{() => <AppShell user={user} onLogout={onLogout}><IndustryPage /></AppShell>}</Route><Route path="/institution">{() => <AppShell user={user} onLogout={onLogout}><InstitutionPage /></AppShell>}</Route><Route path="/opportunity/:id">{() => <AppShell user={user} onLogout={onLogout}><OpportunityDetail user={user} /></AppShell>}</Route><Route component={NotFound} /></Switch>;
}

function AppContent() {
  const [, navigate] = useLocation();
  const [user, setUser] = useState<User | undefined>(); const [token, setToken] = useState(() => localStorage.getItem('skillbridge_token') ?? ''); const current = useGetCurrentUser({ query: { enabled: Boolean(token), queryKey: getGetCurrentUserQueryKey() } });
  useEffect(() => { if (current.data) setUser(current.data); }, [current.data]);
  const onAuth = (next: User, nextToken?: string) => { setUser(next); if (nextToken) setToken(nextToken); };
  const onLogout = () => { localStorage.removeItem('skillbridge_token'); setToken(''); setUser(undefined); navigate('/'); };
  return <TooltipProvider><ErrorBoundary><Router user={user} onAuth={onAuth} onLogout={onLogout} /></ErrorBoundary><Toaster /></TooltipProvider>;
}

function App() {
  return <QueryClientProvider client={queryClient}><AppContent /></QueryClientProvider>;
}

export default App;