from datetime import datetime, timedelta, timezone

from deploy.monitor import parse_access_line, parse_connections, shorten_log, summarise

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 11, 1, 16, 10, 0, tzinfo=IST)


def line(when, ip, path="/api/v1/products", status=200):
    return (f'{when}+05:30 host uvicorn[1]: INFO:     {ip}:60336 - '
            f'"GET {path} HTTP/1.1" {status} OK')


def test_connections_are_read_from_ss():
    output = ("0 0 192.168.1.14:8000 192.168.1.20:50000\n"
              "0 0 [::ffff:192.168.1.14]:8000 [::ffff:192.168.1.21]:50001\n")
    assert parse_connections(output) == ["192.168.1.20", "192.168.1.21"]
    assert parse_connections("") == []


def test_access_line_is_parsed():
    entry = parse_access_line(line("2026-11-01T16:09:16", "192.168.1.20", status=404))
    assert (entry["ip"], entry["path"], entry["status"]) == ("192.168.1.20", "/api/v1/products", 404)
    assert parse_access_line("2026-11-01T16:09:14+05:30 host uvicorn[1]: INFO:     Started") is None


def test_traffic_numbers_ignore_the_server_itself_and_old_lines():
    numbers = summarise([
        line("2026-11-01T16:09:30", "192.168.1.20"),
        line("2026-11-01T16:09:40", "192.168.1.20", status=500),
        line("2026-11-01T16:07:00", "192.168.1.21"),
        line("2026-11-01T16:09:50", "127.0.0.1", "/api/v1/health"),
        line("2026-11-01T16:01:00", "192.168.1.22"),
        "not an access line",
    ], NOW)
    assert numbers == {"requests_last_minute": 2, "visitors_last_5_minutes": 2,
                       "server_errors_last_5_minutes": 1}


def test_log_lines_are_shortened():
    assert shorten_log("2026-11-01T16:09:14+05:30 host uvicorn[1]: INFO:     Started") == "16:09:14  Started"
