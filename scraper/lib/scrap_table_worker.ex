defmodule Scraper.ScrapTableWorker do
  use Oban.Worker, queue: :tables, max_attempts: 10

  alias Scraper.Helper
  alias Scraper.ScrapPageWorker

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"url" => url, "path" => path}}) do
    {:ok, body} = Helper.get(url)
    {:ok, html} = Floki.parse_document(body)
    path = Helper.get_or_create_dir(path)

    max_page =
      case Floki.find(html, "div.numlist") do
        [{_, _, pagination}] ->
          {_, [{"href", link} | _], [_page_number]} = List.last(pagination)

          link
          |> String.split("?page=")
          |> List.last()
          |> String.to_integer()

        _ ->
          1
      end

    Enum.map(1..max_page, fn page ->
      ScrapPageWorker.new(%{
        url: url,
        path: path,
        page: page
      })
    end)
    |> Oban.insert_all()

    :ok
  end
end
