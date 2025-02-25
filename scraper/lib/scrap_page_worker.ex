defmodule Scraper.ScrapPageWorker do
  use Oban.Worker, queue: :pages, max_attempts: 10

  alias Scraper.FileWriter
  alias Scraper.Helper
  alias Scraper.ScrapItemWorker

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"url" => url, "path" => path, "page" => page}}) do
    {:ok, body} = Helper.get(url, page: page)
    {:ok, html} = Floki.parse_document(body)
    path = Helper.get_or_create_file(path, "/page_#{page}.json")

    {:ok, _pid} = FileWriter.start_link(path)

    [{_, _, table_elements}] = Floki.find(html, "table.cnmats")

    {_, _, body_elements} =
      Enum.find(table_elements, fn
        {"tbody", _, _} -> true
        _ -> false
      end)

    item_links =
      Enum.reduce(body_elements, [], fn
        {"tr", _, children}, acc ->
          case hd(children) do
            {_, _, item_link_element} ->
              [{_, [{"href", link}], [_item_name]}] = item_link_element
              [link | acc]

            _ ->
              acc
          end

        _, acc ->
          acc
      end)
      |> Enum.reverse()

    Enum.map(item_links, fn link ->
      ScrapItemWorker.new(%{
        path: path,
        url: link
      })
    end)
    |> Oban.insert_all()

    :ok
  end
end
