import type { Metadata } from "next";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import MuiRtlProvider from '@/components/MuiRtlProvider';
import "../globals.css";

export const metadata: Metadata = {
  title: "Modern Construction ERP",
  description: "Construction ERP Platform",
};

export default async function RootLayout({
  children,
  params: { locale }
}: Readonly<{
  children: React.ReactNode;
  params: { locale: string };
}>) {
  const messages = await getMessages();
  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  return (
    <html lang={locale} dir={dir}>
      <body>
        <NextIntlClientProvider messages={messages}>
          <MuiRtlProvider dir={dir}>
            {children}
          </MuiRtlProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
