FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run as an unprivileged user (defence in depth — container escape != host root).
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY --chown=appuser:appuser . .

COPY entrypoint.sh /entrypoint.sh
# Strip any CR (Windows checkouts) so the shebang resolves to /bin/sh, not /bin/sh\r.
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
