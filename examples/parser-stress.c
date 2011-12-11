#include \
  <complex.h>

int getloadavg(double [], int);

int main()
{
  _Complex double x = 10 + 1*( 1.0iF);

  double y = ( ((sizeof (__real__ (x)) == sizeof (double) || __builtin_classify_type (__real__ (x)) != 8) ? ((sizeof (__real__ (x)) == sizeof (x)) ? (
            __typeof__ (__real__ (
                __typeof__ (*(0 ? (
                      __typeof__ (0 ? (double *) 0 : 
                        (void *) ((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8))))) 0 : (__typeof__ (0 ? (__typeof__
                          ((__typeof__ (x)) 0) *) 0 : (void *) (!((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8)))))) 0))) 0)) creal (x) 
          : (__typeof__ (__real__ (__typeof__ (*(0 ? (__typeof__ (0 ? (double *) 0 : (void *) ((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && 
                              __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8))))) 0 : (__typeof__ (0 ? (__typeof__ ((__typeof__ (x)) 0) *) 0 : (void *) (!((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (
                                __builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8)))))) 0))) 0)) creal (x)) : (sizeof (__real__ (x)) == sizeof (float)) ? 
        ((sizeof (__real__ (x)) == sizeof (x)) ? (__typeof__ (__real__ (__typeof__ (*(0 ? (__typeof__ (0 ? (double *) 0 : (void *) ((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 
                            && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8))))) 0 : (__typeof__ (0 ? (__typeof__ ((__typeof__ (x)) 0) *) 0 : (void *) (!((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (
                              __builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8)))))) 0))) 0)) crealf (x) : (__typeof__ (__real__ (__typeof__ (*(0 ? (__typeof__ (0 ? (double *) 0 : (void *) ((
                          __builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8))))) 0 : (__typeof__ (0 ? (__typeof__ ((__typeof__ (x)) 0) *) 0 
                      : (void *) (!((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8)))))) 0))) 0)) crealf (x)) : 
        ((sizeof (__real__ (x)) == sizeof (x)) ? (__typeof__ (__real__ (__typeof__ (*(0 ? (__typeof__ (0 ? (double *) 0 : (void *) ((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 
                            && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8))))) 0 : (__typeof__ (0 ? (__typeof__ ((__typeof__ (x)) 0) *) 0 : (void *) (!((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || 
                            (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8)))))) 0))) 0)) creall (x) : (__typeof__ (__real__ (__typeof__ (*(0 ? (__typeof__ (0 ? (double *) 0 : (void *) 
                        ((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8))))) 0 : (__typeof__ (0 ? (__typeof__ ((__typeof__ (x)) 0) *) 0 
                        : (void *) (!((__builtin_classify_type ((__typeof__ (x)) 0) == 8 || (__builtin_classify_type ((__typeof__ (x)) 0) == 9 && __builtin_classify_type (__real__ ((__typeof__ (x)) 0)) == 8)))))) 0))) 0)) creall (x))));

  int z;
  __asm__ ("bswap   %0" : "+r" (z));

}
