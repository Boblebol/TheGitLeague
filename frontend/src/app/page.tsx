export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-6xl font-bold text-center mb-4">
          🏀 The Git League
        </h1>
        <p className="text-xl text-center text-muted-foreground mb-8">
          Transform your Git activity into an NBA-style league
        </p>
        <div className="flex gap-4 justify-center">
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">Frontend</h2>
            <p className="text-muted-foreground">Next.js 14 + TypeScript</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">Backend</h2>
            <p className="text-muted-foreground">FastAPI + PostgreSQL</p>
          </div>
        </div>
      </div>
    </main>
  )
}
