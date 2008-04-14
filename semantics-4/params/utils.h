#define CAT_B(a,b)      a ## b
#define CONCAT(a,b)     CAT_B(a,b)
#define CONCAT3(a,b,c)  CONCAT(a,CONCAT(b,c))

#define STR(a)          # a
#define XSTR(a)         STR(a)
