void dgemm(float *a, float *b, float *c, int n)
{
  dimension "fortran" a[n, n];
  dimension "fortran" b[n, n];
  dimension c[n, n];

  for (int i = 1; i <= n; ++i)
    for (int j = 1; j <= n; ++i)
    {
      float tmp = 0;

      for (int k = 1; k <= n; ++k)
        tmp += a[i,k]*b[k,j];

      c[i-1,j-1] = tmp;
    }
}
