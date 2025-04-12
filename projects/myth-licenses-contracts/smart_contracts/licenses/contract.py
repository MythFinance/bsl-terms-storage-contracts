from algopy import (
    Account,
    ARC4Contract,
    BoxMap,
    Bytes,
    StateTotals,
    String,
    Txn,
    UInt64,
    log,
    op,
    subroutine,
)
from algopy.arc4 import abimethod

S = String


@subroutine
def ensure(cond: bool, msg: String) -> None:  # noqa: FBT001
    if not cond:
        log(msg)
        op.err()


class Licenses(
    ARC4Contract,
    state_totals=StateTotals(global_uints=54, global_bytes=10),
):
    def __init__(self) -> None:
        self.admin = Txn.sender
        op.AppGlobal.put(
            b" README 1",
            b"Contract holding additional use grants and change dates for BSL licensed products by Myth Finance.",
        )
        op.AppGlobal.put(
            b" README 2",
            b"Storage keys are prefixed with the product name. Use grants are stored in box storage.",
        )
        op.AppGlobal.put(
            b" README 3",
            b"Change dates are stored in global storage as seconds since 1970-01-01 00:00:00 UTC.",
        )
        self.licenses = BoxMap(String, String, key_prefix=b"")

    @abimethod()
    def add_product(self, name: String, change_date: UInt64) -> None:
        self.admin_only()
        box_key = self.get_use_grant_key(name)
        ensure(box_key not in self.licenses, S("ERR:EXIST"))
        self.set_change_date(name=name, change_date=change_date)
        self.licenses[self.get_use_grant_key(name)] = S("")

    @abimethod()
    def modify_use_grants(
        self, name: String, offset: UInt64, payload: String, final_chunk: bool
    ) -> None:
        # check need resize
        box_key = self.get_use_grant_key(name)
        ensure(box_key in self.licenses, S("ERR:NEXIST"))
        # grow box if needed
        if offset + payload.bytes.length > self.licenses.length(box_key):
            op.Box.resize(box_key.bytes, offset + payload.bytes.length)

        op.Box.splice(box_key.bytes, offset, UInt64(0), payload.bytes)
        # shrink if needed
        if (
            final_chunk
            and self.licenses.length(box_key) > offset + payload.bytes.length
        ):
            op.Box.resize(box_key.bytes, offset + payload.bytes.length)

    @abimethod()
    def modify_change_date(self, name: String, next_change_date: UInt64) -> None:
        self.admin_only()

        box_key = self.get_use_grant_key(name)
        ensure(box_key in self.licenses, S("ERR:NEXIST"))

        # change date can only be moved backwards
        prev_change_date = self.get_change_date(name)
        log(prev_change_date)
        ensure(prev_change_date > next_change_date, S("ERR:LATER"))

        self.set_change_date(name=name, change_date=next_change_date)

    @abimethod()
    def modify_global(self, key: Bytes, value: Bytes) -> None:
        self.admin_only()
        ensure(key[0:1] != b'"', S("ERR:INVLD"))
        op.AppGlobal.put(key, value)

    @abimethod()
    def modify_admin(self, new_admin: Account) -> None:
        self.admin_only()
        self.admin = new_admin

    # --

    @subroutine
    def admin_only(self) -> None:
        ensure(Txn.sender == self.admin, S("ERR:UNAUTH"))

    @subroutine
    def get_change_date(self, name: String) -> UInt64:
        return op.AppGlobal.get_uint64(self.get_change_date_key(name))

    @subroutine
    def set_change_date(self, name: String, change_date: UInt64) -> None:
        op.AppGlobal.put(self.get_change_date_key(name), change_date)

    @subroutine
    def get_use_grant_key(self, name: String) -> String:
        return '"' + name + '" additional use grants'

    @subroutine
    def get_change_date_key(self, name: String) -> Bytes:
        return ('"' + name + '" change date').bytes
