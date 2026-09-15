import type { Metadata } from 'next';
import { SiteFooter } from '@/components/site-footer';
import { SiteHeader } from '@/components/site-header';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://thelibertyarticulator.com'),
  title: {
    default: 'The Liberty Articulator',
    template: '%s — The Liberty Articulator',
  },
  description: 'An independent journal of history, philosophy, and politics, with analysis across every discipline.',
  applicationName: 'The Liberty Articulator',
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    siteName: 'The Liberty Articulator',
    title: 'The Liberty Articulator',
    description: 'Investigating under the microscope of liberty. Analyzing through the telescope of history.',
    url: '/',
    images: [{ url: '/og.png', width: 1200, height: 630, alt: 'The Liberty Articulator — History, Philosophy, Politics' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'The Liberty Articulator',
    description: 'An independent journal of history, philosophy, and politics.',
    images: ['/og.png'],
  },
  icons: { icon: '/favicon.svg' },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
