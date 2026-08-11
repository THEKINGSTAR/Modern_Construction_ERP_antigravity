'use client';

import React from 'react';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import rtlPlugin from 'stylis-plugin-rtl';
import { prefixer } from 'stylis';

const cacheRtl = createCache({
  key: 'muirtl',
  stylisPlugins: [prefixer, rtlPlugin],
});

export default function MuiRtlProvider({ children, dir }: { children: React.ReactNode; dir: string }) {
  if (dir === 'rtl') {
    return <CacheProvider value={cacheRtl}>{children}</CacheProvider>;
  }
  return <>{children}</>;
}
