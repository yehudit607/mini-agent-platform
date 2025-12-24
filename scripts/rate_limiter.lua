-- Atomic sliding window rate limiter for Redis
--
-- This Lua script implements a sliding window rate limiter that:
-- 1. Removes expired entries from the window
-- 2. Counts current requests in the window
-- 3. Either allows the request (adding it to the window) or denies it
--
-- KEYS[1]: rate limit key (e.g., "ratelimit:{tenant_id}")
-- ARGV[1]: window size in seconds
-- ARGV[2]: max requests allowed in the window
-- ARGV[3]: current timestamp in milliseconds
--
-- Returns: {allowed (0/1), remaining requests, retry_after seconds}

local key = KEYS[1]
local window = tonumber(ARGV[1]) * 1000  -- convert to milliseconds
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local window_start = now - window

-- Remove entries older than the window
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

-- Count current requests in the window
local count = redis.call('ZCARD', key)

if count < limit then
    -- Allow request: add timestamp with random suffix for uniqueness
    -- Using now + random ensures unique scores even for concurrent requests
    redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))

    -- Set TTL to 2x window to ensure cleanup
    redis.call('EXPIRE', key, ARGV[1] * 2)

    -- Return: allowed=1, remaining=limit-count-1 (we just added one), retry_after=0
    return {1, limit - count - 1, 0}
else
    -- Deny request: calculate retry_after based on oldest entry
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 0

    if oldest[2] then
        -- Calculate when the oldest entry will expire
        retry_after = math.ceil((oldest[2] + window - now) / 1000)
    else
        -- Fallback to full window if no entries (shouldn't happen)
        retry_after = tonumber(ARGV[1])
    end

    -- Return: allowed=0, remaining=0, retry_after=calculated
    return {0, 0, retry_after}
end
