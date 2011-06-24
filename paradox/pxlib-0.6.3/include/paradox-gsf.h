#ifndef __PARADOX_GSF_H__
#define __PARADOX_GSF_H__

#define PX_HAVE_GSF 0
#if PX_HAVE_GSF
#include <gsf/gsf-input-stdio.h>
#include <gsf/gsf-input-memory.h>
#include <gsf/gsf-output.h>
#endif

#define pxfIOGsf  2

#include <paradox.h>

#if PX_HAVE_GSF
PXLIB_API int PXLIB_CALL
PX_open_gsf(pxdoc_t *pxdoc, GsfInput *gsf);
#endif

#endif
