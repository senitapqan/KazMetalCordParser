defmodule Scraper.Helper do
  @headers [
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  ]

  {"{\"at\": \"2025-02-25T18:54:06.499412Z\", \"error\": \"** (MatchError) no match of right hand side value: []\\n    (scraper 0.1.0) lib/scrap_table_worker.ex:13: Scraper.ScrapTableWorker.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:145: Oban.Queue.Executor.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:77: Oban.Queue.Executor.call/1\\n    (elixir 1.17.1) lib/task/supervised.ex:101: Task.Supervised.invoke_mfa/2\\n    (elixir 1.17.1) lib/task/supervised.ex:36: Task.Supervised.reply/4\\n\", \"attempt\": 1}",
   "{\"at\": \"2025-02-25T18:55:26.000024Z\", \"error\": \"** (MatchError) no match of right hand side value: []\\n    (scraper 0.1.0) lib/scrap_table_worker.ex:13: Scraper.ScrapTableWorker.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:145: Oban.Queue.Executor.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:77: Oban.Queue.Executor.call/1\\n    (elixir 1.17.1) lib/task/supervised.ex:101: Task.Supervised.invoke_mfa/2\\n    (elixir 1.17.1) lib/task/supervised.ex:36: Task.Supervised.reply/4\\n\", \"attempt\": 2}",
   "{\"at\": \"2025-02-25T18:56:46.354285Z\", \"error\": \"** (MatchError) no match of right hand side value: []\\n    (scraper 0.1.0) lib/scrap_table_worker.ex:13: Scraper.ScrapTableWorker.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:145: Oban.Queue.Executor.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:77: Oban.Queue.Executor.call/1\\n    (elixir 1.17.1) lib/task/supervised.ex:101: Task.Supervised.invoke_mfa/2\\n    (elixir 1.17.1) lib/task/supervised.ex:36: Task.Supervised.reply/4\\n\", \"attempt\": 3}",
   "{\"at\": \"2025-02-25T22:30:21.008134Z\", \"error\": \"** (MatchError) no match of right hand side value: {:error, %Req.TransportError{reason: :nxdomain}}\\n    (scraper 0.1.0) lib/scrap_table_worker.ex:9: Scraper.ScrapTableWorker.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:145: Oban.Queue.Executor.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:77: Oban.Queue.Executor.call/1\\n    (elixir 1.17.1) lib/task/supervised.ex:101: Task.Supervised.invoke_mfa/2\\n    (elixir 1.17.1) lib/task/supervised.ex:36: Task.Supervised.reply/4\\n\", \"attempt\": 4}",
   "{\"at\": \"2025-02-25T22:30:54.186978Z\", \"error\": \"** (MatchError) no match of right hand side value: {:error, %Req.TransportError{reason: :nxdomain}}\\n    (scraper 0.1.0) lib/scrap_table_worker.ex:9: Scraper.ScrapTableWorker.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:145: Oban.Queue.Executor.perform/1\\n    (oban 2.19.2) lib/oban/queue/executor.ex:77: Oban.Queue.Executor.call/1\\n    (elixir 1.17.1) lib/task/supervised.ex:101: Task.Supervised.invoke_mfa/2\\n    (elixir 1.17.1) lib/task/supervised.ex:36: Task.Supervised.reply/4\\n\", \"attempt\": 5}"}

  @url_prefix "https://rostmetall.kz"
  def get(url, params \\ []) do
    url = @url_prefix <> url

    case Req.get(url, headers: @headers, params: params) do
      {:ok, %Req.Response{status: 200, body: body}} ->
        {:ok, body}

      {:ok, %Req.Response{status: status}} ->
        {:error, status}

      {:error, error} ->
        {:error, error}
    end
  end

  def get_or_create_file(path, file_name) do
    path = get_or_create_dir(path)
    file_path = Path.join(path, file_name)

    if File.exists?(file_path) == false do
      File.write!(file_path, "")
    end

    file_path
  end

  def get_or_create_dir(path) do
    if File.exists?(path) == false do
      File.mkdir_p!(path)
    end

    path
  end

  def write_to_file(path, content) do
    File.write!(path, content)
  end

  def log(message) do
    dbg(message)
    File.write!("scraper.log", "[#{DateTime.utc_now()}] #{message}\n")
  end
end
