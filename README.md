RIS SIMULATOR SETUP COMMAND
----------------------------
**BLOCK-ALL** :- Block all slots in the specified date rangee i.e. SDATE and EDATE<br/>
**UNBLOCK-ALL** :- Un-Block all slots in the specified date rangee i.e. SDATE and EDATE<br/>

**BLOCK-CURRENT-WEEK** :- Block all slots in the current week. Here, Monday is treated as first day of the week.<br/>
**UNLOCK-CURRENT-WEEK** :- Un-Block all slots in the current week. Here, Monday is treated as first day of the week.<br/>

**BLOCK-TIME-RANGE** :- Block slots for the specified time range in the given day.<br/>
**UNBLOCK-TIME-RANGE** :- Un-Block slots for the specified time range in the given day.<br/>


RIS SIMULATOR COMMAND MACROS
----------------------------
**SDATE** :- Start date<br/>
**EDATE** :- End date<br/>
**MODALITY** :- CR,US,CT,MR<br/>
**STIME** :- Start time (HH:MM)<br/>
**ETIME** :- End time (HH:MM)<br/>

Note: SDATE & EDATE are always referenced for the current date i.e. TODAY.<br/>

SAMPLE COMMANDS
----------------------------
**Block all slots for today**<br/>

    BLOCK-ALL, SDATE=TODAY+0

**Block all slots for tomorrow**<br/>

    BLOCK-ALL, SDATE=TODAY+1

**Block all slots for today & tomorrow**<br/>

    BLOCK-ALL, SDATE=TODAY+0, EDATE=TODAY+1

**Unblock all slots for today**<br/>

    UNBLOCK-ALL, SDATE=TODAY+0

**Un-Block all slots for today & tomorrow**<br/>

    UNBLOCK-ALL, SDATE=TODAY+0, EDATE=TODAY+1

**Block all slots in the current week**<br/>

    BLOCK-CURRENT-WEEK , MODALITY=US

**Un-Block all slots in the current week**<br/>

    UNBLOCK-CURRENT-WEEK , MODALITY=US