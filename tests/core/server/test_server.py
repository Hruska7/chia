from __future__ import annotations

import logging
from typing import Callable, Tuple, cast

import pytest
from packaging.version import Version

from chia.cmds.init_funcs import chia_full_version_str
from chia.full_node.full_node_api import FullNodeAPI
from chia.protocols.protocol_message_types import ProtocolMessageTypes
from chia.protocols.shared_protocol import protocol_version
from chia.protocols.wallet_protocol import RejectHeaderRequest
from chia.server.outbound_message import make_msg
from chia.server.server import ChiaServer
from chia.simulator.block_tools import BlockTools
from chia.simulator.setup_nodes import SimulatorsAndWalletsServices
from chia.simulator.time_out_assert import time_out_assert
from chia.types.peer_info import PeerInfo
from chia.util.ints import uint16, uint32
from tests.connection_utils import connect_and_get_peer


@pytest.mark.asyncio
async def test_duplicate_client_connection(
    two_nodes: Tuple[FullNodeAPI, FullNodeAPI, ChiaServer, ChiaServer, BlockTools], self_hostname: str
) -> None:
    _, _, server_1, server_2, _ = two_nodes
    assert await server_2.start_client(PeerInfo(self_hostname, uint16(server_1._port)), None)
    assert not await server_2.start_client(PeerInfo(self_hostname, uint16(server_1._port)), None)


@pytest.mark.asyncio
@pytest.mark.parametrize("method", [repr, str])
async def test_connection_string_conversion(
    two_nodes_one_block: Tuple[FullNodeAPI, FullNodeAPI, ChiaServer, ChiaServer, BlockTools],
    self_hostname: str,
    method: Callable[[object], str],
) -> None:
    _, _, server_1, server_2, _ = two_nodes_one_block
    peer = await connect_and_get_peer(server_1, server_2, self_hostname)
    # 1000 is based on the current implementation (example below), should be reconsidered/adjusted if this test fails
    # WSChiaConnection(local_type=<NodeType.FULL_NODE: 1>, local_port=50632, local_capabilities=[<Capability.BASE: 1>, <Capability.BLOCK_HEADERS: 2>, <Capability.RATE_LIMITS_V2: 3>], peer_host='127.0.0.1', peer_port=50640, peer_node_id=<bytes32: 566a318f0f656125b4fef0e85fbddcf9bc77f8003d35293c392479fc5d067f4d>, outbound_rate_limiter=<chia.server.rate_limits.RateLimiter object at 0x114a13f50>, inbound_rate_limiter=<chia.server.rate_limits.RateLimiter object at 0x114a13e90>, is_outbound=False, creation_time=1675271096.275591, bytes_read=68, bytes_written=162, last_message_time=1675271096.276271, peer_server_port=50636, active=False, closed=False, connection_type=<NodeType.FULL_NODE: 1>, request_nonce=32768, peer_capabilities=[<Capability.BASE: 1>, <Capability.BLOCK_HEADERS: 2>, <Capability.RATE_LIMITS_V2: 3>], version='', protocol_version='') # noqa
    converted = method(peer)
    print(converted)
    assert len(converted) < 1000


@pytest.mark.asyncio
async def test_connection_versions(
    self_hostname: str, one_wallet_and_one_simulator_services: SimulatorsAndWalletsServices
) -> None:
    [full_node_service], [wallet_service], _ = one_wallet_and_one_simulator_services
    wallet_node = wallet_service._node
    full_node = full_node_service._node
    await wallet_node.server.start_client(
        PeerInfo(self_hostname, uint16(cast(FullNodeAPI, full_node_service._api).server._port)), None
    )
    outgoing_connection = wallet_node.server.all_connections[full_node.server.node_id]
    incoming_connection = full_node.server.all_connections[wallet_node.server.node_id]
    for connection in [outgoing_connection, incoming_connection]:
        assert connection.protocol_version == Version(protocol_version)
        assert connection.version == chia_full_version_str()
        assert connection.get_version_str() == chia_full_version_str()


@pytest.mark.asyncio
async def test_api_not_ready(
    self_hostname: str,
    one_wallet_and_one_simulator_services: SimulatorsAndWalletsServices,
    caplog: pytest.LogCaptureFixture,
) -> None:
    [full_node_service], [wallet_service], _ = one_wallet_and_one_simulator_services
    wallet_node = wallet_service._node
    full_node = full_node_service._node
    await wallet_node.server.start_client(
        PeerInfo(self_hostname, uint16(cast(FullNodeAPI, full_node_service._api).server._port)), None
    )
    wallet_node.log_out()
    assert not wallet_service._api.ready()
    connection = full_node.server.all_connections[wallet_node.server.node_id]

    def request_ignored() -> bool:
        return "API not ready, ignore request: {'data': '0x00000000', 'id': None, 'type': 53}" in caplog.text

    with caplog.at_level(logging.WARNING):
        assert await connection.send_message(
            make_msg(ProtocolMessageTypes.reject_header_request, RejectHeaderRequest(uint32(0)))
        )
        await time_out_assert(10, request_ignored)
