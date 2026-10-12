#include <stdio.h>
void main()
{
     int a, b, c;
     printf("Enter the value of a and b\n");
     scanf("%d%d", &a, &b);
     c = a + b;
     if (a >= b)
     {
          printf("The sum of a and b is %d", c);
     }
}