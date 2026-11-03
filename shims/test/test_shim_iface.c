/* Host-compilable self-test for shim_iface.h's pure address-arithmetic macros
 * AND the shim-home region map (run by `make test`).
 * (The freestanding half is checked by the cross-build + the shim.ld ASSERT,
 * which bounds code+data+bss size; the region-map invariants below are pure
 * macros the linker never sees, so they are enforced HERE.) */
#include <assert.h>
#include <stdio.h>
#include "shim_iface.h"

int main(void) {
    assert(P2ADDR(0x8c010000u) == 0xac010000u);      /* P2 = physical | 0xa0000000 */
    assert(P2ADDR(0x00000000u) == 0xa0000000u);
    assert(SHIM_ERR       == 0x8c014000u);            /* SHIM_BASE + 0x4000 */
    assert(SHIM_CODE_MAX  == 0x4000u);
    assert(SHIM_END       == 0x8c018000u);

    /* Region map: ordered, disjoint, and clear of the KOS stack (a length
     * bump would silently overlap the next slice; nothing else checks
     * these). */
    assert(SHIM_BASE + SHIM_CODE_MAX <= SHIM_ERR);                   /* code+bss | err */
    assert(SHIM_ERR + 16 <= G1_MIRROR);                              /* err (u32[4]) | G1 mirror */
    assert(G1_MIRROR + 0x800 <= MAPLE_MIRROR);                       /* G1 mirror | maple mirror */
    assert(MAPLE_MIRROR + MAPLE_MIRROR_LEN <= MAPLE_TX);             /* maple mirror | tx */
    assert(MAPLE_TX + 0x40 <= MAPLE_RX);                             /* tx | rx */
    assert(MAPLE_RX + 132 <= SHIM_STATE);                            /* rx (DEVINFO reply 132B) | state */
    assert(SHIM_STATE + 32 <= SHIM_BOUNCE);                          /* state (u32[8]) | bounce */
    assert(SHIM_BOUNCE + 2048 <= GD_STACK_BOTTOM);                   /* bounce | GD stack */
    assert(GD_STACK_BOTTOM + 0x1000 <= GD_STACK_TOP);                /* >= 4 KB of stack */
    assert(GD_STACK_TOP == SHIM_END);                                /* shim home ends exactly at SHIM_END */
    assert(SHIM_STATE_GD_BACKEND < 8);              /* inside SHIM_STATE u32[8] */
    assert(SHIM_STATE_LAYOUT_WORD(1, 1) < 8);        /* inside SHIM_STATE u32[8] */
    /* Loader-to-shim slot contract (loader/main.c staging): pad A/B, stick A/B. */
    assert(SHIM_STATE_LAYOUT_WORD(0, 0) == 3 && SHIM_STATE_LAYOUT_WORD(0, 1) == 4);
    assert(SHIM_STATE_LAYOUT_WORD(1, 0) == 5 && SHIM_STATE_LAYOUT_WORD(1, 1) == 6);
    assert(GD_STACK_TOP - GD_STACK_BOTTOM == 0x2000);
    assert(GD_STACK_CANARY != 0);                   /* staging memset is zero */

    printf("shim_iface host self-test: OK (incl. region map)\n");
    return 0;
}
