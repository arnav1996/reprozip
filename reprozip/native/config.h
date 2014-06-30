#ifndef CONFIG_H
#define CONFIG_H

#define WORD_SIZE sizeof(int)

#if !defined(X86) && !defined(X86_64)
#   if defined(__x86_64__) || defined(__x86_64)
#       define X86_64
#   elif defined(__i386__) || defined(__i386) || defined(_M_I86) || defined(_M_IX86)
#       define I386
#   else
#       error Unrecognized architecture!
#   endif
#endif

#ifndef __X32_SYSCALL_BIT
#define __X32_SYSCALL_BIT 0x40000000
#endif

#endif
