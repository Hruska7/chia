from typing import List
from chia.wallet.puzzles.load_clvm import load_clvm
from chia.types.blockchain_format.program import Program
from chia.util.ints import uint64
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.wallet.puzzles.cat_loader import CAT_MOD

SINGLETON_MOD: Program = load_clvm("singleton_top_layer_v1_1.clvm")
SINGLETON_LAUNCHER: Program = load_clvm("singleton_launcher.clvm")
DAO_LOCKUP_MOD: Program = load_clvm("dao_lockup.clvm")
DAO_PROPOSAL_TIMER_MOD: Program = load_clvm("dao_proposal_timer.clvm")
DAO_PROPOSAL_MOD: Program = load_clvm("dao_proposal.clvm")
DAO_TREASURY_MOD: Program = load_clvm("dao_treasury.clvm")
P2_SINGLETON_MOD: Program = load_clvm("p2_singleton_or_delayed_puzhash.clvm")
DAO_FINISHED_STATE: Program = load_clvm("dao_finished_state.clvm")
DAO_RESALE_PREVENTION: Program = load_clvm("dao_resale_prevention_layer.clvm")
DAO_CAT_TAIL: Program = load_clvm("genesis_by_coin_id_or_proposal.clvm")

DAO_TREASURY_MOD_HASH = DAO_TREASURY_MOD.get_tree_hash()
DAO_PROPOSAL_MOD_HASH = DAO_PROPOSAL_MOD.get_tree_hash()
DAO_PROPOSAL_TIMER_MOD_HASH = DAO_PROPOSAL_TIMER_MOD.get_tree_hash()
DAO_LOCKUP_MOD_HASH = DAO_LOCKUP_MOD.get_tree_hash()
CAT_MOD_HASH = CAT_MOD.get_tree_hash()
SINGLETON_MOD_HASH = SINGLETON_MOD.get_tree_hash()
SINGLETON_LAUNCHER_PUZHASH = SINGLETON_LAUNCHER.get_tree_hash()


def get_treasury_puzzle(
    treasury_id: bytes32,
    cat_tail: bytes32,
    current_cat_issuance: uint64,
    proposal_pass_percentage: uint64,
    proposal_timelock: uint64,
) -> Program:
    # SINGLETON_STRUCT
    # TREASURY_MOD_HASH
    # PROPOSAL_MOD_HASH
    # PROPOSAL_TIMER_MOD_HASH
    # LOCKUP_MOD_HASH
    # CAT_MOD_HASH
    # CAT_TAIL
    # CURRENT_CAT_ISSUANCE
    # PROPOSAL_PASS_PERCENTAGE
    # PROPOSAL_TIMELOCK
    singleton_struct: Program = Program.to((SINGLETON_MOD_HASH, (treasury_id, SINGLETON_LAUNCHER_PUZHASH)))
    puzzle = DAO_TREASURY_MOD.curry(
        singleton_struct,
        DAO_TREASURY_MOD_HASH,
        DAO_PROPOSAL_MOD_HASH,
        DAO_PROPOSAL_TIMER_MOD_HASH,
        DAO_LOCKUP_MOD_HASH,
        CAT_MOD_HASH,
        cat_tail,
        current_cat_issuance,
        proposal_pass_percentage,
        proposal_timelock,
    )
    return puzzle


def get_lockup_puzzle(
    cat_tail: bytes32,
    previous_votes_list: List[bytes32],
    proposal_timelock: uint64,
    innerpuz: Program
) -> Program:
    # PROPOSAL_MOD_HASH
    # SINGLETON_MOD_HASH
    # SINGLETON_LAUNCHER_PUZHASH
    # LOCKUP_MOD_HASH
    # CAT_MOD_HASH
    # CAT_TAIL
    # PREVIOUS_VOTES  ; "active votes" list
    # LOCKUP_TIME
    # INNERPUZ
    puzzle: Program = DAO_LOCKUP_MOD.curry(
        DAO_PROPOSAL_MOD_HASH,
        SINGLETON_MOD_HASH,
        SINGLETON_LAUNCHER_PUZHASH,
        DAO_LOCKUP_MOD_HASH,
        CAT_MOD_HASH,
        cat_tail,
        previous_votes_list,  # TODO: maybe format check this in this function
        proposal_timelock,
        innerpuz,
    )
    return puzzle


def get_proposal_puzzle(
    proposal_id: bytes32,
    cat_tail: bytes32,
    proposal_pass_percentage: uint64,
    treasury_id: bytes32,
    proposal_timelock: uint64,
    votes_sum: int,
    total_votes: uint64,
    innerpuz: Program
) -> Program:
    # SINGLETON_STRUCT  ; ((SINGLETON_MOD_HASH, (SINGLETON_ID, LAUNCHER_PUZZLE_HASH)))
    # PROPOSAL_MOD_HASH
    # PROPOSAL_TIMER_MOD_HASH
    # CAT_MOD_HASH
    # TREASURY_MOD_HASH
    # LOCKUP_MOD_HASH
    # CAT_TAIL
    # PROPOSAL_PASS_PERCENTAGE
    # TREASURY_ID
    # PROPOSAL_TIMELOCK
    # VOTES_SUM  ; yes votes are +1, no votes are -1
    # TOTAL_VOTES  ; how many people responded
    # INNERPUZ  ; this is what runs if this proposal is successful
    singleton_struct: Program = Program.to((SINGLETON_MOD_HASH, (proposal_id, SINGLETON_LAUNCHER_PUZHASH)))
    puzzle = DAO_PROPOSAL_MOD.curry(
        singleton_struct,
        DAO_PROPOSAL_MOD_HASH,
        DAO_PROPOSAL_TIMER_MOD_HASH,
        CAT_MOD_HASH,
        DAO_TREASURY_MOD_HASH,
        DAO_LOCKUP_MOD_HASH,
        cat_tail,
        proposal_pass_percentage,
        treasury_id,
        proposal_timelock,
        votes_sum,
        total_votes,
        innerpuz,
    )
    return puzzle


def get_proposal_timer_puzzle(
    cat_tail: bytes32,
    proposal_timelock: uint64,
    proposal_pass_percentage: uint64,
    proposal_id: bytes32,
    treasury_id: bytes32,
) -> Program:
    # PROPOSAL_MOD_HASH
    # PROPOSAL_TIMER_MOD_HASH
    # CAT_MOD_HASH
    # CAT_TAIL
    # PROPOSAL_TIMELOCK
    # PROPOSAL_PASS_PERCENTAGE
    # MY_PARENT_SINGLETON_STRUCT  ; ((SINGLETON_MOD_HASH, (PROPOSAL_SINGLETON_ID, LAUNCHER_PUZZLE_HASH)))
    # TREASURY_ID
    parent_singleton_struct: Program = Program.to((SINGLETON_MOD_HASH, (proposal_id, SINGLETON_LAUNCHER_PUZHASH)))
    puzzle: Program = DAO_PROPOSAL_TIMER_MOD.curry(
        DAO_PROPOSAL_MOD_HASH,
        DAO_PROPOSAL_TIMER_MOD_HASH,
        CAT_MOD_HASH,
        cat_tail,
        proposal_timelock,
        proposal_pass_percentage,
        parent_singleton_struct,
        treasury_id,
    )
    return puzzle


def generate_cat_tail(genesis_coin_id: bytes32, treasury_id: bytes32) -> Program:
    # GENESIS_ID
    # DAO_TREASURY_ID
    # SINGLETON_MOD_HASH
    # SINGLETON_LAUNCHER_PUZHASH
    # DAO_PROPOSAL_MOD_HASH
    puzzle = DAO_CAT_TAIL.curry(
        genesis_coin_id,
        treasury_id,
        SINGLETON_MOD_HASH,
        SINGLETON_LAUNCHER_PUZHASH,
        DAO_PROPOSAL_MOD
    )
    return puzzle


def curry_singleton(singleton_id: bytes32, innerpuz: bytes32) -> Program:
    singleton_struct = Program.to((SINGLETON_MOD_HASH, (singleton_id, SINGLETON_LAUNCHER_PUZHASH)))
    return SINGLETON_MOD.curry(singleton_struct, innerpuz)
