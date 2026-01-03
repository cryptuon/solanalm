"""
Cache Key Patterns for SolanaLM

Centralized cache key definitions to prevent key collisions and ensure consistency.
"""


class CacheKeys:
    """Cache key patterns with TTL recommendations"""

    # Node Registry Cache (5 min TTL)
    NODE_BY_ID = "node:{node_id}"                    # Single node data
    NODE_LIST = "nodes:list"                          # All nodes list
    NODE_BY_MODEL = "nodes:model:{model}"            # Nodes supporting a model
    NODE_ONLINE = "nodes:online"                      # Set of online node IDs
    NODE_BY_TYPE = "nodes:type:{node_type}"          # Nodes by type

    # Node Metrics (30 sec TTL - frequently updated)
    NODE_METRICS = "metrics:node:{node_id}"          # Per-node metrics
    NETWORK_STATS = "metrics:network"                 # Aggregated network stats

    # Rate Limiting (sliding window)
    RATE_LIMIT = "ratelimit:{identifier}:{endpoint}"  # Rate limit counter
    RATE_LIMIT_BLOCKED = "ratelimit:blocked:{identifier}"  # Blocked identifiers

    # User Sessions (configurable TTL, typically 24h)
    USER_SESSION = "session:{session_id}"            # User session data
    API_KEY_VALID = "apikey:{key_hash}"              # Validated API key cache
    USER_BY_WALLET = "user:wallet:{wallet_address}"  # User lookup by wallet

    # Training Rounds (match round duration)
    TRAINING_ROUND = "training:round:{round_id}"     # Active training round
    TRAINING_PARTICIPANTS = "training:participants:{round_id}"  # Round participants

    # Privacy Circuits (match circuit lifetime, typically 5-10 min)
    CIRCUIT = "circuit:{circuit_id}"                 # Onion routing circuit
    NODE_PUBLIC_KEY = "nodekey:{node_id}"            # Node public keys for encryption

    # Payment Cache (short TTL for pending, longer for confirmed)
    PAYMENT_PENDING = "payment:pending:{signature}"  # Pending payment status
    PAYMENT_STATUS = "payment:status:{signature}"    # Payment confirmation status
    WALLET_BALANCE = "wallet:balance:{address}"      # Cached wallet balance (30s TTL)

    # Locks (distributed locks for concurrent operations)
    LOCK_NODE_REGISTER = "lock:node:register:{node_id}"
    LOCK_TRAINING_ROUND = "lock:training:round:{round_id}"
    LOCK_PAYMENT = "lock:payment:{signature}"

    @classmethod
    def node(cls, node_id: str) -> str:
        return cls.NODE_BY_ID.format(node_id=node_id)

    @classmethod
    def nodes_by_model(cls, model: str) -> str:
        return cls.NODE_BY_MODEL.format(model=model)

    @classmethod
    def nodes_by_type(cls, node_type: str) -> str:
        return cls.NODE_BY_TYPE.format(node_type=node_type)

    @classmethod
    def node_metrics(cls, node_id: str) -> str:
        return cls.NODE_METRICS.format(node_id=node_id)

    @classmethod
    def rate_limit(cls, identifier: str, endpoint: str = "default") -> str:
        return cls.RATE_LIMIT.format(identifier=identifier, endpoint=endpoint)

    @classmethod
    def rate_limit_blocked(cls, identifier: str) -> str:
        return cls.RATE_LIMIT_BLOCKED.format(identifier=identifier)

    @classmethod
    def session(cls, session_id: str) -> str:
        return cls.USER_SESSION.format(session_id=session_id)

    @classmethod
    def api_key(cls, key_hash: str) -> str:
        return cls.API_KEY_VALID.format(key_hash=key_hash)

    @classmethod
    def user_by_wallet(cls, wallet_address: str) -> str:
        return cls.USER_BY_WALLET.format(wallet_address=wallet_address)

    @classmethod
    def training_round(cls, round_id: str) -> str:
        return cls.TRAINING_ROUND.format(round_id=round_id)

    @classmethod
    def circuit(cls, circuit_id: str) -> str:
        return cls.CIRCUIT.format(circuit_id=circuit_id)

    @classmethod
    def wallet_balance(cls, address: str) -> str:
        return cls.WALLET_BALANCE.format(address=address)

    @classmethod
    def payment_status(cls, signature: str) -> str:
        return cls.PAYMENT_STATUS.format(signature=signature)


# Default TTLs in seconds
class CacheTTL:
    """Default TTL values for different cache types"""

    NODE_DATA = 300          # 5 minutes
    NODE_METRICS = 30        # 30 seconds
    NODE_LIST = 60           # 1 minute
    NETWORK_STATS = 30       # 30 seconds

    RATE_LIMIT_WINDOW = 60   # 1 minute sliding window
    RATE_LIMIT_BLOCK = 300   # 5 minute block duration

    USER_SESSION = 86400     # 24 hours
    API_KEY_CACHE = 3600     # 1 hour

    TRAINING_ROUND = 3600    # 1 hour (adjust based on round duration)

    CIRCUIT = 600            # 10 minutes
    NODE_KEY = 3600          # 1 hour

    WALLET_BALANCE = 30      # 30 seconds
    PAYMENT_STATUS = 300     # 5 minutes

    LOCK_DEFAULT = 30        # 30 seconds
    LOCK_PAYMENT = 120       # 2 minutes
