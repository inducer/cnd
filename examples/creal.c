#include <complex.h>
#include <tgmath.h>
#include <stdio.h>

int main()
{
  dimension a[5; 5];
  CND_DECL_ALLOC_STACK(complex double, a);

  a[0; 10] = 10 + 5*I;
  printf("%f %f\n", creal(a[0; 10]), cimag(a[0; 10]));
}
