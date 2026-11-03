// Ghidra headless script: disassemble at the Naomi header entrypoint and print
// the first 32 instructions. Sanity-checks that SuperH4:LE:32 decodes the
// boot binary imported at base 0x8c020000. Usage:
//   kit/scripts/ghidra/run.sh script DisasmEntry.java <entry-hex>
// <entry-hex> = the game's entry PC, 0x-prefixed (0x + port_def.ENTRY_PC).
//
// Note: disasm_entry.py is the Jython-API version (Ghidra <=10 / reference).
// This Java version is used with Ghidra 12+ which dropped Jython headless support.
//@category Cleopatra
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class DisasmEntry extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        long entry = Long.decode(a[0]);
        Address addr = toAddr(entry);
        new DisassembleCommand(addr, null, true).applyTo(currentProgram, monitor);
        Instruction ins = currentProgram.getListing().getInstructionAt(addr);
        int n = 0;
        while (ins != null && n < 32) {
            println(ins.getAddress() + "  " + ins);
            ins = ins.getNext();
            n++;
        }
        if (n == 0) {
            println(String.format("FAIL: no instructions decoded at 0x%08x", entry));
        }
    }
}
