import './globals.css';
import { ReactNode } from 'react';
import { ThemeProvider } from 'next-themes';

export const metadata = { title: 'Person Detection Webdash', description: 'Realtime person detection alerts' };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="dark">
          <div className="min-h-screen bg-background text-foreground">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
