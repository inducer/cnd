void dgemm(float *a, float *b, float *c, int n)
{
  dimension "fortran" a[n, n];
  dimension "fortran" b[n, n];
  dimension c[n, n];

  for (int i = 1; i <= n; ++i)
    for (int j = 1; j <= n; ++j)
    {
      float tmp = 0;

      for (int k = 1; k <= n; ++k)
        tmp += a[i,k]*b[k,j];

      c[i-1,j-1] = tmp;
    }
}

void mpole(double *mpole, int n)
{
  dimension "fortran" mpole[0:n, -n:];

  for (int i = 0; i <= n; ++i)
    for (int j = -n; j <= n; ++j)
    {
      printf("%f\n", mpole[i ,j]);
    }
}
