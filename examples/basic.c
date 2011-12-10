#include <complex.h>
#include <tgmath.h>
#include <stdlib.h>
#include <stdio.h>

#if __STDC_VERSION__ < 199901L
#error This is a C99 file. Use '-std=c99' for gcc or a similar flag for other compilers.
#error (If running with just 'cnd' and not 'cndcc', pass --cpp="cpp -std=c99".)
#endif

void sgemm(float *a, float *b, float *c, int n)
{
  dimension "fortran" a(n, n);
  dimension "fortran" b(n, n);
  dimension c(n, n);

  for (int i = 1; i <= n; ++i)
    for (int j = 1; j <= n; ++j)
    {
      float tmp = 0;

      for (int k = 1; k <= n; ++k)
        tmp += a(i,k)*b(k,j);

      c(i-1,j-1) = tmp;
    }
}

#ifdef YO
int DUDE;
#endif

void print_mpole(complex double *mpole, int n)
{
  dimension "fortran" mpole(0:n, -n:n);

  unsigned long int x = 0;

  for (int i = 0; i <= n; ++i)
    for (int j = -n; j <= n; ++j)
    {
      printf("%f\n", mpole(i, j));
    }
}

int main()
{
  int n = 17;
  dimension "fortran" mpole(0:n, -n:n);

  complex double *mpole = malloc(nitemsof(mpole)*sizeof(complex double));
  if (!mpole)
    perror("alloc mpole");

  for (long i = lboundof(mpole, 0); i <= uboundof(mpole, 0); ++i)
    for (long j = lboundof(mpole, 1); j <= uboundof(mpole, 1); ++j)
      mpole(i,j) = i+j;

  print_mpole(mpole, n);

  free(mpole);

  // same code as above, now using CnD shorthand:

  dimension "fortran" mpole2(0:n, -n:n);
  CND_DECL_ALLOC_HEAP(complex double, mpole2);
  if (!mpole2)
    perror("alloc mpole2");

  CND_FOR_AXIS(i, mpole2, 0)
    CND_FOR_AXIS(j, mpole2, 1)
      mpole2(i,j) = i*j;

  print_mpole(mpole2, n);

  free(mpole2);
}
