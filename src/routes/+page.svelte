<script>
	import Fuse from 'fuse.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import BackTop from '$lib/components/BackTop.svelte';

	let { data } = $props();

	const keys = [
		{
			name: 'title',
			weight: 3
		},
		{
			name: 'tags',
			weight: 2
		},
		{
			name: 'description',
			weight: 1
		}
	];
	const searchOptions = {
		keys: keys,
		includeScore: true,
		includeMatches: true,
		useExtendedSearch: true,
		minMatchCharLength: 1
	};

	let fuseIndex = null;
	let fuseInstance = null;
	let searchResults = $state([]);
	let formatedData = $derived(formatData(data.data));
	let flattenedData = $derived(flattenData(formatedData));

	$effect(() => {
		if (flattenedData) {
			fuseIndex = Fuse.createIndex(searchOptions.keys, flattenedData);
			fuseInstance = new Fuse(flattenedData, searchOptions, fuseIndex);
		}
	});

	function handleKeyPress(event) {
		if (event.key === '/' && event.target.tagName !== 'INPUT') {
			event.preventDefault();
			searchInputRef?.focus();
		}
	}
	onMount(() => {
		if (browser) {
			document.addEventListener('keydown', handleKeyPress);
		}
	});

	onDestroy(() => {
		if (browser) {
			document.removeEventListener('keydown', handleKeyPress);
		}
	});

	function formatData(data) {
		if (!data) return [];

		let result = formatDataWithPath(data, '');
		result = sortDataByType(result);
		return result;

		function formatDataWithPath(items, parentPath = '') {
			if (!Array.isArray(items)) return items;

			return items.map((item) => {
				if (item.type === 'folder' && Array.isArray(item.children)) {
					const hasChildFolders = item.children.some((child) => child.type === 'folder');
					return {
						...item,
						path: parentPath,
						hasChildren: hasChildFolders,
						children: formatDataWithPath(item.children, parentPath ? [parentPath, item.title].join('%') : item.title)
					};
				}

				return {
					...item,
					path: parentPath
				};
			});
		}

		function sortDataByType(items) {
			if (!Array.isArray(items)) return items;

			const sortedItems = [...items].sort((a, b) => {
				if (a.type === 'folder' && b.type !== 'folder') return -1;
				if (b.type === 'folder' && a.type !== 'folder') return 1;
				return a.title.localeCompare(b.title);
			});

			return sortedItems.map((item) => {
				if (item.type === 'folder' && Array.isArray(item.children)) {
					return {
						...item,
						children: sortDataByType(item.children)
					};
				}
				return item;
			});
		}
	}

	function flattenData(data) {
		if (!Array.isArray(data)) return [];

		const flattened = [];

		function flatten(items) {
			for (const item of items) {
				if (item.type === 'folder' && item.children) {
					flatten(item.children);
				} else {
					flattened.push(item);
				}
			}
		}
		flatten(data);
		return flattened;
	}

	let searchTerm = $state('');
	let searchInputRef;
	let selectedFolder = $state([]);
	let filteredResults = $derived(getFilteredResults());

	function handleSearch() {
		if (!fuseInstance || searchTerm.length < searchOptions.minMatchCharLength) {
			searchResults = [];
			return;
		}
		selectedFolder = [];
		searchResults = searchTerm ? fuseInstance.search(searchTerm) : flattenedData;
	}

	function highlightText(text, matches) {
		if (!matches || matches.length === 0) return text;

		let result = '';
		let lastIndex = 0;

		const sortedMatches = [...matches].sort((a, b) => a[0] - b[0]);

		sortedMatches.forEach(([start, end]) => {
			result += text.slice(lastIndex, start);
			result += `<span class="bg-accent">${text.slice(start, end + 1)}</span>`;
			lastIndex = end + 1;
		});

		result += text.slice(lastIndex);
		return result;
	}

	function getFilteredResults() {
		if (selectedFolder.length === 0) {
			if (searchResults.length > 0) {
				return searchResults;
			}
			return flattenedData;
		}
		let folder = formatedData;
		for (let i = 0; i < selectedFolder.length && folder; i++) {
			const element = selectedFolder[i];
			folder = folder.find((item) => item.title === element);
			folder = folder?.children || [];
		}
		return folder || [];
	}

	function handleFolderClick(folderPath) {
		selectedFolder = folderPath ? folderPath.split('%') : [];
		searchResults = [];
		searchTerm = '';
		isAsideVisible = false;
	}

	let isAsideVisible = $state(false);
</script>

<svelte:head>
	<title>Collector</title>
</svelte:head>

<nav class="fixed top-0 z-50 w-full border-b border-base-300 bg-base-100/90 shadow-sm">
	<div class="px-3 py-3 lg:px-5 lg:pl-3">
		<div class="flex items-center justify-between">
			<div class="flex items-center justify-start rtl:justify-end">
				<label class="swap swap-rotate focus:outline-none sm:hidden">
					<input
						type="checkbox"
						onclick={() => {
							isAsideVisible = !isAsideVisible;
						}}
						bind:checked={isAsideVisible}
					/>
					<!-- hamburger icon -->
					<span class="swap-off icon-[mynaui--menu-solid] fill-current" style="width: 32px; height: 32px;"></span>
					<!-- close icon -->
					<span class="swap-on icon-[iconamoon--close-light] fill-current" style="width: 32px; height: 32px;"></span>
				</label>
				<a href="#" class="group ms-2 flex md:me-24">
					<img src="./favicon.svg" class="me-2 w-20 sm:w-8" alt="Collector Logo" />
					<span class="text-md hidden self-center font-semibold sm:block">Collector</span>
				</a>
			</div>

			<div class="flex items-center justify-end">
				<label class="input input-bordered flex h-10 items-center">
					<span class="icon-[fluent--search-12-regular]" style="width: 24px; height: 24px;"></span>
					<input
						id="searchInput"
						type="text"
						placeholder="Type / to search"
						class="input input-ghost w-full max-w-xs focus:border-none"
						oninput={(e) => handleSearch(e.target.value)}
						bind:this={searchInputRef}
						bind:value={searchTerm}
					/>
				</label>
			</div>
			<div class="flex items-center">
				<div class="ms-3 flex items-center">
					<!-- svelte-ignore a11y_label_has_associated_control -->
					<label class="swap swap-rotate" data-toggle-theme="dark" data-act-class="swap-active">
						<!-- sun icon -->
						<span class="swap-off icon-[prime--sun]" style="width: 32px; height: 32px;"></span>
						<!-- moon icon -->
						<span class="swap-on icon-[solar--moon-bold-duotone]" style="width: 32px; height: 32px;"></span>
					</label>
				</div>
				<div>
					<a href="https://github.com/wefantasy/collector" target="_blank" aria-label="github" class="ms-3 flex items-center">
						<span class="icon-[octicon--mark-github-24]" style="width: 30px; height: 30px;"></span>
					</a>
				</div>
			</div>
		</div>
	</div>
</nav>

{#if isAsideVisible}
	<div
		class="fixed inset-0 z-30 bg-black/50 transition-opacity sm:hidden"
		onclick={() => {
			isAsideVisible = !isAsideVisible;
		}}
	></div>
{/if}

<aside
	class="fixed left-0 top-0 z-40 h-screen {isAsideVisible
		? 'translate-x-0'
		: '-translate-x-full'} border-r border-base-300 bg-base-100 pt-20 transition-transform sm:w-48 sm:translate-x-0"
	aria-label="Sidebar"
>
	<div class="h-full overflow-y-auto px-3 pb-4">
		<ul class="menu space-y-1">
			<li>
				<a
					href="#"
					class="group flex cursor-pointer items-center hover:bg-base-200 {selectedFolder.join('%') === '' ? 'bg-base-200' : ''}"
					onclick={() => handleFolderClick('')}
				>
					<span class="icon-[clarity--folder-open-line]" style="width: 20px; height: 20px;"></span>
					<span>All Item</span>
				</a>
			</li>
			{#each formatedData as item}
				{#if item.type === 'folder'}
					<li>
						<a
							href="#"
							class="group flex cursor-pointer items-center hover:bg-base-200 {selectedFolder.join('%') === item.title ? 'bg-base-200' : ''}"
							onclick={() => handleFolderClick(item.title)}
						>
							<span class="icon-[clarity--folder-open-solid]" style="width: 20px; height: 20px;"></span>
							<span>{item.title}</span>
						</a>
					</li>
				{/if}
			{/each}
		</ul>
	</div>
</aside>

<div class="p-4 sm:ml-48">
	<div class="mt-14 rounded-lg p-4">
		<div class="breadcrumbs text-sm text-secondary">
			<ul>
				<li>
					<a href="#" class="cursor-pointer" onclick={() => handleFolderClick('')}> Root </a>
				</li>

				{#each selectedFolder as item, i}
					<li>
						<a href="#" class="cursor-pointer" onclick={() => handleFolderClick(selectedFolder.slice(0, i + 1).join('%'))}>
							{item}
						</a>
					</li>
				{/each}
			</ul>
		</div>

		<div class="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4 md:grid-cols-8 md:gap-4">
			{#each filteredResults as item}
				{#if searchResults.length > 0}
					<div class="col-span-2 rounded-lg border border-base-200 bg-base-100 p-3">
						<a class="group flex cursor-pointer items-center gap-2" href={item.item.url} target="_blank">
							<img
								src={`https://www.google.com/s2/favicons?domain=${item.item.url}&sz=32`}
								alt="favicon"
								class="h-8 w-8 rounded-full transition-transform duration-500 group-hover:rotate-[360deg]"
							/>
							<div class="min-w-0 flex-1">
								<h2 class="text-md overflow-hidden truncate whitespace-nowrap">
									{@html item.matches?.find((m) => m.key === 'title')
										? highlightText(item.item.title, item.matches.find((m) => m.key === 'title').indices)
										: item.item.title}
								</h2>
								<p class="overflow-hidden truncate whitespace-nowrap text-sm text-secondary">
									{item.item.url}
								</p>
							</div>
						</a>
						<div class="tooltip" data-tip={item.item.description}>
							<p class="mt-2 line-clamp-3 text-justify text-sm text-secondary underline decoration-dotted underline-offset-2">
								{@html item.matches?.find((m) => m.key === 'description')
									? highlightText(item.item.description, item.matches.find((m) => m.key === 'description').indices)
									: item.item.description}
							</p>
						</div>
					</div>
				{:else if item.type === 'folder'}
					<a
						class="group col-span-1 flex cursor-pointer flex-col items-center justify-center"
						href="#"
						onclick={() => handleFolderClick(item.path + '%' + item.title)}
					>
						<span class="icon-[ph--folder-open-fill] transition-transform duration-300 group-hover:scale-110" style="width: 100px; height: 100px;"></span>

						<p class="w-full overflow-hidden truncate whitespace-nowrap text-center text-sm text-secondary">{item.title}</p>
					</a>
				{:else}
					<div class="col-span-2 rounded-lg border border-base-200 bg-base-100 p-3">
						<a class="group flex cursor-pointer items-center gap-2" href={item.url} target="_blank">
							<img
								src={`https://www.google.com/s2/favicons?domain=${item.url}&sz=32`}
								alt="favicon"
								class="h-8 w-8 rounded-full transition-transform duration-500 group-hover:rotate-[360deg]"
							/>
							<div class="min-w-0 flex-1">
								<h2 class="text-md overflow-hidden truncate whitespace-nowrap">{item.title}</h2>
								<p class="overflow-hidden truncate whitespace-nowrap text-sm text-secondary">{item.url}</p>
							</div>
						</a>
						<div class="tooltip" data-tip={item.description}>
							<p class="mt-2 line-clamp-3 text-justify text-sm text-secondary underline decoration-dotted underline-offset-2">{item.description}</p>
						</div>
					</div>
				{/if}
			{/each}
		</div>
	</div>

	<BackTop />

	<div class="mt-4 rounded-lg">
		<div class="text-center">
			© 2025 <a href="https://github.com/wefantasy/collector" target="_blank" aria-label="github" class="link-hover link link-primary">collector</a>, Design by
			<a href="https://github.com/wefantasy" target="_blank" aria-label="github" class="link-hover link link-primary">wefantasy</a>
		</div>
	</div>
</div>
